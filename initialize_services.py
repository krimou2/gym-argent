from app import create_app
from app.models import Plan, PlanOption, db

def initialize_services():
    app = create_app()
    with app.app_context():
        try:
            # First ensure a base plan exists
            base_plan = Plan.query.filter_by(name="Base Services Plan").first()
            if not base_plan:
                base_plan = Plan(
                    name="Base Services Plan",
                    duration="monthly",
                    base_price=0,
                    description="Container for all individual services"
                )
                db.session.add(base_plan)
                db.session.commit()
                print("✓ Created base services plan")

            services = [
                ("Personal Training", 60, "trainer"),
                ("Nutrition Consultation", 50, "nutritionist"),
                ("Physiotherapy Session", 70, "physiotherapist"),
                ("Group Fitness Class", 20, "trainer")
            ]
            
            added_count = 0
            updated_count = 0
            
            for name, price, specialty in services:
                existing = PlanOption.query.filter_by(option_name=name).first()
                
                if not existing:
                    # Create new service
                    service = PlanOption(
                        plan_id=base_plan.id,
                        option_name=name,
                        option_price=price,
                        hours_included=1,
                        specialty=specialty
                    )
                    db.session.add(service)
                    print(f"✓ Added service: {name} (${price}, {specialty})")
                    added_count += 1
                elif existing.specialty != specialty:
                    # Update existing service's specialty if incorrect
                    existing.specialty = specialty
                    db.session.add(existing)
                    print(f"↻ Updated specialty for: {name} (now {specialty})")
                    updated_count += 1
            
            db.session.commit()
            
            print(f"\nOperation complete:")
            print(f"- Added {added_count} new services")
            print(f"- Updated {updated_count} existing services")
            if (added_count + updated_count) < len(services):
                print(f"- {len(services) - (added_count + updated_count)} services were already correct")

            # Verify all services have specialties
            missing_specialty = PlanOption.query.filter(PlanOption.specialty.is_(None)).count()
            if missing_specialty:
                print(f"\n⚠ Warning: Found {missing_specialty} services without specialties")
                print("Run this in flask shell to fix:")
                print("""
from app.models import PlanOption, db
PlanOption.query.filter(PlanOption.specialty.is_(None)).update({'specialty': 'trainer'})
db.session.commit()
                """)

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error during initialization: {str(e)}")
            print("Check your database connection and model definitions")
        finally:
            # Final verification
            print("\nCurrent services in database:")
            for service in PlanOption.query.order_by(PlanOption.option_name).all():
                print(f"- {service.option_name} (${service.option_price}, {service.specialty or 'NO SPECIALTY'})")

if __name__ == '__main__':
    initialize_services()