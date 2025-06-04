from django.core.management.base import BaseCommand
from wqi_app.models import WaterQualityMeasurement
from wqi_app.utils.fuzzy_mamdani import calculate_mamdani_wqi
from wqi_app.utils.fuzzy_sugeno import calculate_sugeno_wqi
from wqi_app.utils.fuzzy_storet import calculate_storet_score
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update Storet, Mamdani, and Sugeno WQI values for existing measurements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without saving to database',
        )
        parser.add_argument(
            '--methods',
            nargs='+',
            type=str,
            default=['storet', 'mamdani', 'sugeno'],
            help='Specify which WQI methods to update (storet, mamdani, sugeno)',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        methods = [m.lower() for m in options.get('methods', [])]
        
        # Validate methods
        valid_methods = ['storet', 'mamdani', 'sugeno']
        for method in methods:
            if method not in valid_methods:
                self.stdout.write(self.style.ERROR(f'Invalid method: {method}. Valid options are: {", ".join(valid_methods)}'))
                return
                
        self.stdout.write(self.style.SUCCESS(f'Will update the following WQI methods: {", ".join(methods)}'))
        
        # Get all measurements
        measurements = WaterQualityMeasurement.objects.all()
        count = measurements.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No measurements found in database.'))
            return
            
        self.stdout.write(self.style.SUCCESS(f'Found {count} measurements to update.'))
        
        # Track success and errors
        success_count = 0
        error_count = 0
        
        # Process in batches with transaction to ensure efficiency
        try:
            with transaction.atomic():
                for idx, measurement in enumerate(measurements, 1):
                    if idx % 100 == 0:
                        self.stdout.write(f'Processing {idx}/{count}...')
                    
                    update_fields = []
                    try:
                        # Calculate and update Storet WQI
                        if 'storet' in methods:
                            storet_result = calculate_storet_score(measurement)
                            
                            # Determine storet_class based on wqi_value if not provided by the function
                            if 'wqi_class' not in storet_result:
                                # Determine storet class based on wqi_value
                                wqi_value = storet_result['wqi_value']
                                if wqi_value >= 90:
                                    storet_class = "A"
                                elif wqi_value >= 70:
                                    storet_class = "B"
                                elif wqi_value >= 50:
                                    storet_class = "C"
                                elif wqi_value >= 25:
                                    storet_class = "D"
                                else:
                                    storet_class = "E"
                            else:
                                storet_class = storet_result['wqi_class']
                            
                            # Output current and new values
                            current_class = getattr(measurement, 'storet_class', '-')
                            self.stdout.write(
                                f'ID: {measurement.id} - '
                                f'Original Storet: {measurement.storet_wqi:.2f} ({measurement.storet_category}) [{current_class}] → '
                                f'New: {storet_result["wqi_value"]:.2f} ({storet_result["wqi_category"]}) [{storet_class}]'
                            )
                            
                            if not dry_run:
                                measurement.storet_wqi = storet_result['wqi_value']
                                measurement.storet_category = storet_result['wqi_category'].lower()
                                measurement.storet_class = storet_class
                                update_fields.extend(['storet_wqi', 'storet_category', 'storet_class'])
                        
                        # Calculate and update Mamdani WQI
                        if 'mamdani' in methods:
                            mamdani_result = calculate_mamdani_wqi(measurement)
                            self.stdout.write(
                                f'ID: {measurement.id} - '
                                f'Original Mamdani: {measurement.mamdani_wqi:.2f} ({measurement.mamdani_category}) → '
                                f'New: {mamdani_result["wqi_value"]:.2f} ({mamdani_result["wqi_category"]})'
                            )
                            if not dry_run:
                                measurement.mamdani_wqi = mamdani_result['wqi_value']
                                measurement.mamdani_category = mamdani_result['wqi_category'].lower()
                                update_fields.extend(['mamdani_wqi', 'mamdani_category'])
                        
                        # Calculate and update Sugeno WQI
                        if 'sugeno' in methods:
                            sugeno_result = calculate_sugeno_wqi(measurement)
                            self.stdout.write(
                                f'ID: {measurement.id} - '
                                f'Original Sugeno: {measurement.sugeno_wqi:.2f} ({measurement.sugeno_category}) → '
                                f'New: {sugeno_result["wqi_value"]:.2f} ({sugeno_result["wqi_category"]})'
                            )
                            if not dry_run:
                                measurement.sugeno_wqi = sugeno_result['wqi_value']
                                measurement.sugeno_category = sugeno_result['wqi_category'].lower()
                                update_fields.extend(['sugeno_wqi', 'sugeno_category'])
                        
                        # Save all updates at once
                        if not dry_run and update_fields:
                            measurement.save(update_fields=update_fields)
                        
                        success_count += 1
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error processing measurement {measurement.id}: {str(e)}'))
                        logger.error(f'Error updating WQI for measurement {measurement.id}: {str(e)}')
                        error_count += 1
                
                if dry_run:
                    self.stdout.write(self.style.WARNING('DRY RUN - No changes were saved to database'))
                    transaction.set_rollback(True)
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Transaction failed: {str(e)}'))
            logger.error(f'Transaction failed during WQI update: {str(e)}')
            return
        
        # Final report
        self.stdout.write(self.style.SUCCESS(
            f'Update complete: {success_count} successful, {error_count} failed'
        ))