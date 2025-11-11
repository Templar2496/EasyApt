from slugify import slugify
from datetime import datetime
from app.db import SessionLocal
from app.models import Clinic, Provider, ProviderHours

def ensure_seed():
    db = SessionLocal()
    try:
        # clinic
        clinic = db.query(Clinic).filter(Clinic.name=="Downtown Health").first()
        if not clinic:
            clinic = Clinic(name="Downtown Health", address="123 Main St", phone="555-0100")
            db.add(clinic); db.flush()

        # provider
        slug = slugify("Dr Alice Carter")
        prov = db.query(Provider).filter(Provider.slug==slug).first()
        if not prov:
            prov = Provider(name="Dr. Alice Carter", specialty="Family Medicine", slug=slug, clinic_id=clinic.id)
            db.add(prov); db.flush()

        # Mon–Fri 9:00–17:00 hours (only add if missing)
        for wd in range(0,5):
            exists = db.query(ProviderHours).filter_by(
                provider_id=prov.id, weekday=wd, start_minute=9*60, end_minute=17*60
            ).first()
            if not exists:
                db.add(ProviderHours(provider_id=prov.id, weekday=wd, start_minute=9*60, end_minute=17*60))

        db.commit()
        print("Seed ok (idempotent).")
    finally:
        db.close()

if __name__ == "__main__":
    ensure_seed()

