# database.py
from pymongo import MongoClient, DESCENDING
from datetime import datetime
from typing import Dict, List, Any
import os
import logging
from dotenv import load_dotenv
from datatypes import LeadStatus, AdSpendIntensity, RiskLevel   

load_dotenv()

# ========================================
# CONFIG & LOGGER
# ========================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "fb_leads"
COLLECTION_NAME = "leads"

# ========================================
# DATABASE CLIENT (singleton)
# ========================================
class MongoDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = MongoClient(MONGO_URI)
            cls._instance.db = cls._instance.client[DB_NAME]
            cls._instance.collection = cls._instance.db[COLLECTION_NAME]
            cls._instance._setup_indexes()
            cls._instance._apply_schema_validator()   # <-- NEW
        return cls._instance

    # ------------------------------------------------------------------
    # Indexes (exactly the fields that have index:true in TS)
    # ------------------------------------------------------------------
    def _setup_indexes(self):
        try:
            self.collection.create_index("library_id", unique=True)
            self.collection.create_index("advertiser")
            self.collection.create_index("service")
            self.collection.create_index("status")
            self.collection.create_index("probability", DESCENDING)
            self.collection.create_index("created_at", DESCENDING)
            logger.info("Indexes created / verified")
        except Exception as e:
            logger.warning(f"Index setup failed (may already exist): {e}")

    # ------------------------------------------------------------------
    # MongoDB JSON Schema (run once – safe to call many times)
    # ------------------------------------------------------------------
    def _apply_schema_validator(self):
        validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["advertiser", "library_id", "service", "probability"],
                "properties": {
                    "advertiser": {"bsonType": "string"},
                    "facebook_link": {"bsonType": ["string", "null"]},
                    "website_link": {"bsonType": ["string", "null"]},
                    "contact": {"bsonType": ["string", "null"]},
                    "library_id": {"bsonType": "string"},
                    "probability": {
                        "bsonType": "int",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "service": {"bsonType": "string"},
                    "reasoning": {"bsonType": ["string", "null"]},
                    "issues": {"bsonType": ["string", "null"]},
                    "estimated_daily_orders": {"bsonType": "string"},
                    "ad_spend_intensity": {
                        "enum": [e.value for e in AdSpendIntensity]
                    },
                    "cart_abandon_risk": {
                        "enum": [e.value for e in RiskLevel]
                    },
                    "estimated_monthly_revenue": {"bsonType": "string"},
                    "dm_open_rate_prediction": {"bsonType": "string"},
                    "status": {
                        "enum": [e.value for e in LeadStatus]
                    },
                    "tags": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"}
                    },
                    "pitch": {"bsonType": ["string", "null"]},
                    "whatsapp_link": {"bsonType": ["string", "null"]},
                    "notes": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "object",
                            "required": ["text", "at"],
                            "properties": {
                                "text": {"bsonType": "string"},
                                "at": {"bsonType": "date"}
                            }
                        }
                    },
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"},
                    "__v": {"bsonType": "int"}          # optional optimistic concurrency
                }
            }
        }

        try:
            self.db.command("collMod", COLLECTION_NAME, validator=validator)
            logger.info("JSON schema validator applied")
        except Exception as e:
            # Collection may not exist yet – create it with the validator
            try:
                self.db.create_collection(
                    COLLECTION_NAME,
                    validator=validator
                )
                logger.info("Collection created with validator")
            except Exception as e2:
                logger.debug(f"Validator already exists or error: {e2}")

    def get_collection(self):
        return self.collection


# ========================================
# LEAD MODEL – validation + defaults
# ========================================
class LeadModel:
    @staticmethod
    def _trim(value: Any) -> str:
        return str(value).strip() if value is not None else ""

    @staticmethod
    def validate(lead: Dict) -> Dict:
        """Enforce the exact TS schema (trim, defaults, enums, ranges)"""
        # ---------- REQUIRED ----------
        required = ["advertiser", "library_id", "service", "probability"]
        for f in required:
            if f not in lead:
                raise ValueError(f"Missing required field: {f}")

        # ---------- STRING TRIMMING ----------
        string_fields = [
            "advertiser", "facebook_link", "website_link", "contact",
            "service", "reasoning", "issues", "pitch", "whatsapp_link"
        ]
        for f in string_fields:
            if f in lead:
                lead[f] = LeadModel._trim(lead[f]) or None   # keep null if empty

        # ---------- PROBABILITY ----------
        prob = lead.get("probability", 0)
        try:
            prob = int(prob)
            if not (0 <= prob <= 100):
                raise ValueError("probability must be 0-100")
        except (TypeError, ValueError):
            raise ValueError("probability must be an integer 0-100")
        lead["probability"] = prob

        # ---------- ENUMS ----------
        lead["status"] = lead.get("status", LeadStatus.NEW.value)
        if lead["status"] not in [e.value for e in LeadStatus]:
            raise ValueError(f"Invalid status: {lead['status']}")

        lead["ad_spend_intensity"] = lead.get(
            "ad_spend_intensity", AdSpendIntensity.LOW.value
        )
        if lead["ad_spend_intensity"] not in [e.value for e in AdSpendIntensity]:
            raise ValueError(f"Invalid ad_spend_intensity: {lead['ad_spend_intensity']}")

        lead["cart_abandon_risk"] = lead.get(
            "cart_abandon_risk", RiskLevel.LOW.value
        )
        if lead["cart_abandon_risk"] not in [e.value for e in RiskLevel]:
            raise ValueError(f"Invalid cart_abandon_risk: {lead['cart_abandon_risk']}")

        # ---------- DEFAULTS ----------
        lead.setdefault("estimated_daily_orders", "Unknown")
        lead.setdefault("estimated_monthly_revenue", "< ৳150K")
        lead.setdefault("dm_open_rate_prediction", "Low (<30%)")
        lead.setdefault("tags", [])
        lead.setdefault("notes", [])

        # ---------- TIMESTAMPS ----------
        now = datetime.utcnow()
        if "created_at" not in lead:
            lead["created_at"] = now
        lead["updated_at"] = now

        # ---------- OPTIONAL version key ----------
        lead.setdefault("__v", 0)

        return lead

    # ------------------------------------------------------------------
    # Helper used by pitch generator (kept unchanged – just updated keys)
    # ------------------------------------------------------------------
    @staticmethod
    def default_pitch_row(lead: Dict) -> Dict:
        return {
            "Advertiser": lead.get("advertiser", "Unknown"),
            "issues": lead.get("issues", ""),
            "Est. Daily Orders": lead.get("estimated_daily_orders", "Unknown"),
            "Est. Monthly Revenue": lead.get("estimated_monthly_revenue", "< ৳150K"),
            "Contact": lead.get("contact", ""),
            "Website Link": lead.get("website_link", "")
        }


# ========================================
# DATABASE OPERATIONS
# ========================================
class LeadDB:
    def __init__(self):
        self.collection = MongoDB().get_collection()

    # ------------------------------------------------------------------
    # UPSERT (replace_one + upsert)
    # ------------------------------------------------------------------
    def upsert_lead(self, lead: Dict) -> Dict[str, Any]:
        try:
            lead = LeadModel.validate(lead)
            library_id = lead["library_id"]

            result = self.collection.replace_one(
                {"library_id": library_id},
                lead,
                upsert=True
            )
            return {
                "saved": 1 if result.upserted_id else 0,
                "updated": result.matched_count,
                "library_id": library_id
            }
        except Exception as e:
            logger.error(f"Upsert failed for {lead.get('library_id')}: {e}")
            return {"saved": 0, "updated": 0, "error": str(e)}

    # ------------------------------------------------------------------
    # BULK UPSERT
    # ------------------------------------------------------------------
    def bulk_upsert(self, leads: List[Dict]) -> Dict[str, Any]:
        results = {"saved": 0, "updated": 0, "skipped": 0, "errors": []}
        for lead in leads:
            try:
                res = self.upsert_lead(lead)
                results["saved"] += res["saved"]
                results["updated"] += res["updated"]
            except Exception:
                results["skipped"] += 1
                results["errors"].append(lead.get("library_id", "unknown"))
        return results

    # ------------------------------------------------------------------
    # HIGH PRIORITY
    # ------------------------------------------------------------------
    def get_high_priority(self, min_prob: int = 65, limit: int = 50) -> List[Dict]:
        cursor = self.collection.find({
            "probability": {"$gte": min_prob},
            "contact": {"$nin": ["", None]},
            "status": {"$ne": LeadStatus.CLIENT.value}
        }).sort("probability", DESCENDING).limit(limit)
        return list(cursor)

    # ------------------------------------------------------------------
    # STATUS UPDATE + NOTE
    # ------------------------------------------------------------------
    def update_status(self, library_id: str, status: str, note: str = "") -> bool:
        if status not in [e.value for e in LeadStatus]:
            raise ValueError(f"Invalid status: {status}")

        update: Dict[str, Any] = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        if note:
            update["$push"] = {"notes": {"text": note.strip(), "at": datetime.utcnow()}}

        result = self.collection.update_one(
            {"library_id": library_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}},
            **({"$push": {"notes": {"text": note.strip(), "at": datetime.utcnow()}}} if note else {})
        )
        return result.modified_count > 0

    # ------------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------------
    def search(self, query: str) -> List[Dict]:
        regex = {"$regex": query, "$options": "i"}
        cursor = self.collection.find({
            "$or": [
                {"advertiser": regex},
                {"contact": regex}
            ]
        }).limit(20)
        return list(cursor)

    # ------------------------------------------------------------------
    # STATS
    # ------------------------------------------------------------------
    def get_stats(self) -> Dict:
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        stats = {item["_id"]: item["count"] for item in self.collection.aggregate(pipeline)}
        stats["total"] = sum(stats.values())
        return stats