from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, WaterQualityMeasurementForm, LocationForm
from .models import WaterQualityMeasurement, Location
from .utils.fuzzy_mamdani import calculate_mamdani_wqi
from .utils.fuzzy_sugeno import calculate_sugeno_wqi
from .utils.fuzzy_storet import calculate_storet_score
from django.db.models import Avg
from django.views.decorators.http import require_POST
import folium
import pandas as pd
from django.http import HttpResponse, Http404
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.contrib.auth import logout
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from django.conf import settings
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully!')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def dashboard(request):
    measurements = WaterQualityMeasurement.objects.all().order_by('-date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        measurements = measurements.filter(
            Q(location__name__icontains=search_query) |
            Q(mamdani_category__icontains=search_query) |
            Q(sugeno_category__icontains=search_query) |
            Q(storet_category__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(measurements, 10)  # Show 10 measurements per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculations
    avg_mamdani_wqi = measurements.aggregate(Avg('mamdani_wqi'))['mamdani_wqi__avg'] or 0
    avg_sugeno_wqi = measurements.aggregate(Avg('sugeno_wqi'))['sugeno_wqi__avg'] or 0
    avg_storet_score = measurements.aggregate(Avg('storet_score'))['storet_score__avg'] or 0
    
    context = {
        'page_obj': page_obj,
        'total_measurements': measurements.count(),
        'avg_mamdani_wqi': avg_mamdani_wqi,
        'avg_sugeno_wqi': avg_sugeno_wqi,
        'avg_storet_score': avg_storet_score,
    }
    
    return render(request, 'wqi_app/dashboard.html', context)

@login_required
def add_measurement(request):
    if request.method == 'POST':
        form = WaterQualityMeasurementForm(request.POST)
        if form.is_valid():
            measurement = form.save(commit=False)
            measurement.user = request.user
            
            try:
                # Hitung dengan ketiga metode
                mamdani = calculate_mamdani_wqi(measurement)
                sugeno = calculate_sugeno_wqi(measurement)
                storet = calculate_storet_score(measurement)
                
                # Pastikan hasil perhitungan valid
                def validate_result(result, method_name):
                    if not result.get('wqi_value') or not result.get('wqi_category'):
                        raise ValueError(f"Hasil perhitungan {method_name} tidak valid: {result}")
                    return result
                
                mamdani = validate_result(mamdani, "Mamdani")
                sugeno = validate_result(sugeno, "Sugeno")
                storet = validate_result(storet, "STORET")
                
                # Simpan hasil (pastikan lowercase untuk kategori)
                measurement.mamdani_wqi = mamdani['wqi_value']
                measurement.mamdani_category = mamdani['wqi_category'].lower()
                measurement.sugeno_wqi = sugeno['wqi_value']
                measurement.sugeno_category = sugeno['wqi_category'].lower()
                measurement.storet_wqi = storet['wqi_value']
                measurement.storet_category = storet['wqi_category'].lower()
                measurement.storet_score = storet.get('storet_score', 0)
                measurement.storet_class = storet.get('storet_class', 'Tidak Diketahui')
                
                measurement.save()
                messages.success(request, 'Pengukuran berhasil ditambahkan!')
                return redirect('dashboard')
                
            except ValueError as e:
                messages.error(request, f'Data tidak valid: {str(e)}')
            except Exception as e:
                messages.error(request, f'Terjadi kesalahan sistem: {str(e)}')
                # Log error untuk debugging (opsional)
                import logging
                logging.error(f"Error saat menambah pengukuran: {str(e)}")
            
            return render(request, 'wqi_app/measurement_form.html', {'form': form})
    
    else:
        form = WaterQualityMeasurementForm()
    
    return render(request, 'wqi_app/measurement_form.html', {'form': form})

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.urls import reverse
from decimal import Decimal
import json
from folium import IFrame, Popup, Html
from .models import Location, WaterQualityMeasurement

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

from django.shortcuts import render
from django.urls import reverse
from .models import Location
import folium
from folium.plugins import MarkerCluster

@login_required
def map_view(request):
    locations = Location.objects.all()
    
    m = folium.Map(
        location=[-6.2, 106.8],
        zoom_start=12
    )
    
    marker_cluster = MarkerCluster().add_to(m)
    
    for loc in locations:
        detail_url = reverse('location_detail', kwargs={'pk': loc.id})  # RELATIVE URL SAJA
        
        popup_content = f"""
<div style='width:250px;font-family:Arial,sans-serif;text-align:center;'>
    <h4 style='margin:0 0 5px 0;padding:0;'>{loc.name}</h4>
    <hr style='margin:5px 0;border-color:#eee;'>
    <a href="{reverse('location_detail', kwargs={'pk': loc.id})}" 
       target="_parent"
       style="display:inline-block;width:100%;background:#4CAF50;color:white;
              text-decoration:none;border:none;padding:8px;border-radius:4px;
              cursor:pointer;font-size:14px;margin-top:5px;">
       View Details
    </a>
</div>
"""

        
        folium.Marker(
            [float(loc.latitude), float(loc.longitude)],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=loc.name
        ).add_to(marker_cluster)

    return render(request, 'wqi_app/map_view.html', {
        'map': m._repr_html_()
    })

@login_required
def location_detail(request, pk):  # Parameter harus 'pk' bukan 'location_id'
    location = get_object_or_404(Location, pk=pk)
    measurements = WaterQualityMeasurement.objects.filter(
        location=location,
        user=request.user
    ).order_by('-date')
    
    return render(request, 'wqi_app/location_detail.html', {
        'location': location,
        'measurements': measurements
    })

def location_measurements(request, pk):
    location = get_object_or_404(Location, pk=pk)
    measurements = WaterQualityMeasurement.objects.filter(
        location=location
    ).order_by('-date')
    
    return render(request, 'wqi_app/location_measurements.html', {
        'location': location,
        'measurements': measurements
    })

@login_required
def export_measurements_to_excel(request):
    try:
        # Query dengan select_related untuk optimasi
        measurements = WaterQualityMeasurement.objects.select_related('user', 'location').all()
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Water Quality Data"
        
        # Header dengan styling
        headers = [
            "No", "User", "Location", "Date", 
            "pH", "DO (mg/L)", "BOD (mg/L)", "COD (mg/L)", 
            "Total Coliform", 
            "Mamdani WQI", "Mamdani Status",
            "Sugeno WQI", "Sugeno Status",
            "STORET WQI", "STORET Score", "STORET Status", "STORET Class"
        ]
        ws.append(headers)
        
        # Set lebar kolom
        column_widths = [5, 15, 20, 20, 10, 10, 10, 10, 15, 12, 15, 12, 15, 12, 12, 15, 20]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + i)].width = width
        
        # Format tanggal
        date_format = "%Y-%m-%d %H:%M"
        
        for idx, measurement in enumerate(measurements, 1):
            row = [
                idx,
                measurement.user.get_full_name() or measurement.user.username,
                measurement.location.name,
                measurement.date.strftime(date_format),
                round(measurement.ph, 2) if measurement.ph is not None else "-",
                round(measurement.do, 2) if measurement.do is not None else "-",
                round(measurement.bod, 2) if measurement.bod is not None else "-",
                round(measurement.cod, 2) if measurement.cod is not None else "-",
                round(measurement.total_coliform, 2) if measurement.total_coliform is not None else "-",
                round(measurement.mamdani_wqi, 2) if measurement.mamdani_wqi is not None else "-",
                measurement.mamdani_category.title() if measurement.mamdani_category else "-",
                round(measurement.sugeno_wqi, 2) if measurement.sugeno_wqi is not None else "-",
                measurement.sugeno_category.title() if measurement.sugeno_category else "-",
                round(measurement.storet_wqi, 2) if measurement.storet_wqi is not None else "-",
                measurement.storet_score if measurement.storet_score is not None else "-",
                measurement.storet_category.title() if measurement.storet_category else "-",
                measurement.storet_class if measurement.storet_class else "-"
            ]
            ws.append(row)
        
        # Buat response
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"water_quality_export_{timestamp}.xlsx"
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f"attachment; filename={filename}"
        wb.save(response)
        
        return response
    
    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        return HttpResponse("Terjadi kesalahan saat mengekspor data", status=500)
    
def export_measurements_to_pdf(request, id):
    try:
        # Pastikan measurement ada
        try:
            measurement = WaterQualityMeasurement.objects.select_related('user', 'location').get(id=id)
        except ObjectDoesNotExist:
            raise Http404("Pengukuran tidak ditemukan")

        # Buat response PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="water_quality_{id}.pdf"'

        # Buat dokumen
        doc = SimpleDocTemplate(
            response,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )

        elements = []
        styles = getSampleStyleSheet()

        # Style tambahan
        styles.add(ParagraphStyle(
            name='CenterTitle',
            parent=styles['Title'],
            alignment=TA_CENTER,
            spaceAfter=0.5*inch
        ))

        # Judul
        elements.append(Paragraph('Laporan Kualitas Air', styles['CenterTitle']))

        # Informasi dasar
        info_data = [
            ['ID Pengukuran', str(measurement.id)],
            ['Lokasi', measurement.location.name],
            ['Tanggal', measurement.date.strftime('%d %B %Y %H:%M')],
            ['Penginput', measurement.user.get_full_name() or measurement.user.username]
        ]

        info_table = Table(info_data, colWidths=[1.5*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (0,-1), 'RIGHT'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
            ('LEFTPADDING', (1,0), (1,-1), 10),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.5*inch))

        # Parameter kualitas air
        elements.append(Paragraph('Parameter Kualitas Air', styles['Heading2']))
        
        param_data = [
            ['Parameter', 'Nilai', 'Status'],
            ['pH', str(measurement.ph), getattr(measurement, 'ph_status', '-')],
            ['DO (mg/L)', str(measurement.do), getattr(measurement, 'do_status', '-')],
            ['BOD (mg/L)', str(measurement.bod), getattr(measurement, 'bod_status', '-')],
            ['COD (mg/L)', str(measurement.cod), getattr(measurement, 'cod_status', '-')],
            ['Total Coliform', str(measurement.total_coliform), getattr(measurement, 'tc_status', '-')]
        ]

        param_table = Table(param_data, colWidths=[2*inch, 1*inch, 1.5*inch])
        param_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#D9E1F2')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ]))
        elements.append(param_table)
        elements.append(Spacer(1, 0.5*inch))

        # Hasil Analisis
        elements.append(Paragraph('Hasil Analisis', styles['Heading2']))
        
        analysis_data = [
            ['Metode', 'Nilai', 'Kategori'],
            ['Mamdani', 
             f"{measurement.mamdani_wqi:.2f}" if measurement.mamdani_wqi else '-', 
             measurement.mamdani_category or '-'],
            ['Sugeno', 
             f"{measurement.sugeno_wqi:.2f}" if measurement.sugeno_wqi else '-', 
             measurement.sugeno_category or '-'],
            ['STORET', 
             str(measurement.storet_score) if measurement.storet_score else '-', 
             measurement.storet_category or '-']
        ]

        analysis_table = Table(analysis_data, colWidths=[1.5*inch, 1*inch, 1.5*inch])
        analysis_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#70AD47')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#E2EFDA')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ]))
        elements.append(analysis_table)

        # Build PDF
        doc.build(elements)
        return response

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return HttpResponse(
            "Terjadi kesalahan saat membuat laporan PDF. Silakan coba lagi atau hubungi administrator.",
            status=500
        )

@login_required
def add_location(request):
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('location_list')  
    else:
        form = LocationForm()
    
    return render(request, 'wqi_app/add_location.html', {'form': form})

@login_required
def location_list(request):
    location_list = Location.objects.all()
    paginator = Paginator(location_list, 10)  # 10 per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'wqi_app/location_list.html', {
        'locations': page_obj,
        'page_obj': page_obj,
    })

def measurement_detail(request, measurement_id):  # Ganti parameter menjadi measurement_id
    measurement = get_object_or_404(WaterQualityMeasurement, pk=measurement_id)
    
    # Debugging: Cetak nilai kategori ke console
    print(f"Debug - Kategori Sugeno: {measurement.sugeno_category}")
    print(f"Debug - Kategori Mamdani: {measurement.mamdani_category}")
    print(f"Debug - Kategori STORET: {measurement.storet_category}")
    
    context = {
        'measurement': measurement,
        'title': 'Detail Pengukuran'
    }
    return render(request, 'wqi_app/measurement_detail.html', context)

@require_POST
def logout_view(request):
    """
    View untuk menangani proses logout
    """
    logout(request)  # Melakukan logout
    messages.success(request, 'Anda telah berhasil logout.')  # Pesan sukses dalam Bahasa Indonesia
    return redirect('login')  # Mengarahkan ke halaman login menggunakan nama URL