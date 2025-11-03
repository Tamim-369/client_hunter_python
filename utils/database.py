from pymongo import MongoClient, DESCENDING
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
import logging
from dotenv import load_dotenv 
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
# DATABASE CLIENT
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
        return cls._instance

    def _setup_indexes(self):
        """Ensure unique + fast query indexes"""
        try:
            self.collection.create_index("library_id", unique=True)
            self.collection.create_index("contact")
            self.collection.create_index("probability", DESCENDING)
            self.collection.create_index("status")
            self.collection.create_index("created_at", DESCENDING)
            logger.info("MongoDB indexes created/verified")
        except Exception as e:
            logger.warning(f"Index setup failed (may already exist): {e}")

    def get_collection(self):
        return self.collection


# ========================================
# LEAD MODEL (SCHEMA + VALIDATION)
# ========================================
class LeadModel:
    @staticmethod
    def validate(lead: Dict) -> Dict:
        """Enforce schema + clean data"""
        required = ["advertiser", "library_id", "probability"]
        for field in required:
            if field not in lead:
                raise ValueError(f"Missing required field: {field}")

        # Clean strings
        for key in ["advertiser", "facebook_link", "website_link", "contact", "service", "issues"]:
            if key in lead:
                lead[key] = str(lead[key]).strip()

        # Ensure types
        lead["probability"] = int(lead.get("probability", 0))
        lead["status"] = lead.get("status", "new")
        lead["notes"] = lead.get("notes", [])
        lead["tags"] = lead.get("tags", ["fb-ad"])

        # Timestamps
        now = datetime.utcnow()
        if "created_at" not in lead:
            lead["created_at"] = now
        lead["updated_at"] = now

        return lead

    @staticmethod
    def default_pitch_row(lead: Dict) -> Dict:
        """Used by generate_pitch_and_link() — avoids circular import"""
        return {
            "Advertiser": lead.get("advertiser", "Unknown"),
            "issues": lead.get("issues", ""),
            "Est. Daily Orders": lead.get("Est. Daily Orders", "Unknown"),
            "Est. Monthly Revenue": lead.get("Est. Monthly Revenue", "< ৳150K"),
            "Contact": lead.get("contact", ""),
            "Website Link": lead.get("website_link", "")
        }


# ========================================
# DATABASE OPERATIONS
# ========================================
class LeadDB:
    def __init__(self):
        self.collection = MongoDB().get_collection()

    def upsert_lead(self, lead: Dict) -> Dict[str, int]:
        """Insert or update lead by library_id"""
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

    def bulk_upsert(self, leads: List[Dict]) -> Dict[str, int]:
        """Upsert many leads"""
        results = {"saved": 0, "updated": 0, "skipped": 0, "errors": []}
        for lead in leads:
            try:
                res = self.upsert_lead(lead)
                results["saved"] += res["saved"]
                results["updated"] += res["updated"]
            except:
                results["skipped"] += 1
                results["errors"].append(lead.get("library_id", "unknown"))
        return results

    def get_high_priority(self, min_prob: int = 65, limit: int = 50) -> List[Dict]:
        """Get top leads for outreach"""
        cursor = self.collection.find({
            "probability": {"$gte": min_prob},
            "contact": {"$nin": ["", None]},
            "status": {"$ne": "client"}
        }).sort("probability", DESCENDING).limit(limit)
        return list(cursor)

    def update_status(self, library_id: str, status: str, note: str = "") -> bool:
        """Mark as contacted, audit, etc."""
        update = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        if note:
            update["$push"] = {"notes": {"text": note, "at": datetime.utcnow()}}
        result = self.collection.update_one(
            {"library_id": library_id},
            {"$set": update}
        )
        return result.modified_count > 0

    def search(self, query: str) -> List[Dict]:
        """Search by advertiser or contact"""
        regex = {"$regex": query, "$options": "i"}
        cursor = self.collection.find({
            "$or": [
                {"advertiser": regex},
                {"contact": regex}
            ]
        }).limit(20)
        return list(cursor)

    def get_stats(self) -> Dict:
        """Dashboard stats"""
        pipeline = [
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        stats = {item["_id"]: item["count"] for item in self.collection.aggregate(pipeline)}
        stats["total"] = sum(stats.values())
        return stats