from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='get_status')
def get_status(value, param_name):
    """
    Filter universal untuk status parameter kualitas air
    """
    param_filters = {
        'ph': get_ph_status,
        'do': get_do_status,
        'bod': get_bod_status,
        'cod': get_cod_status,
        'total_coliform': get_tc_status
    }
    
    if param_name in param_filters:
        return param_filters[param_name](value)
    return mark_safe('<span class="badge bg-secondary">-</span>')

## ====================== KATEGORI WQI ====================== ##
@register.filter(name='get_category_color')
def get_category_color(category):
    """
    Mengembalikan kelas warna Bootstrap berdasarkan kategori WQI
    Versi lebih robust dengan penanganan null dan case sensitivity
    """
    if not category:
        return 'secondary'
    
    category = str(category).strip().lower()
    color_map = {
        'excellent': 'success',
        'baik sekali': 'success',
        'good': 'info',
        'baik': 'info',
        'fair': 'warning',
        'sedang': 'warning',
        'poor': 'danger',
        'buruk': 'danger',
        'sangat buruk': 'dark'
    }
    return color_map.get(category, 'secondary')

@register.filter(name='get_category_badge')
def get_category_badge(category):
    """
    Mengembalikan badge lengkap dengan warna dan teks kategori
    """
    color_class = get_category_color(category)
    return mark_safe(f'<span class="badge bg-{color_class}">{category.title() if category else "-"}</span>')

## ====================== PARAMETER KUALITAS AIR ====================== ##

def _safe_float_conversion(value):
    """Helper function untuk konversi aman ke float"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

@register.filter(name='get_ph_status')
def get_ph_status(value):
    """
    Mengembalikan badge HTML untuk status pH dengan standar lebih ketat
    """
    ph_value = _safe_float_conversion(value)
    if ph_value is None:
        return mark_safe('<span class="badge bg-secondary">-</span>')
    
    if 6.5 <= ph_value <= 8.5:
        return mark_safe('<span class="badge bg-success" title="pH Optimal">Normal</span>')
    elif 6.0 <= ph_value < 6.5 or 8.5 < ph_value <= 9.0:
        return mark_safe('<span class="badge bg-warning" title="pH Diluar Range Optimal">Sedang</span>')
    else:
        return mark_safe('<span class="badge bg-danger" title="pH Berbahaya">Tidak Normal</span>')

@register.filter(name='get_do_status')
def get_do_status(value):
    """
    Mengembalikan badge HTML untuk status DO dengan kriteria lebih detail
    """
    do_value = _safe_float_conversion(value)
    if do_value is None:
        return mark_safe('<span class="badge bg-secondary">-</span>')
    
    if do_value >= 6:
        return mark_safe('<span class="badge bg-success" title="Oksigen Terlarut Tinggi">Baik</span>')
    elif 4 <= do_value < 6:
        return mark_safe('<span class="badge bg-warning" title="Oksigen Terlarut Cukup">Cukup</span>')
    elif 2 <= do_value < 4:
        return mark_safe('<span class="badge bg-warning" title="Oksigen Terlarut Rendah">Rendah</span>')
    else:
        return mark_safe('<span class="badge bg-danger" title="Oksigen Terlarut Sangat Rendah">Buruk</span>')

@register.filter(name='get_bod_status')
def get_bod_status(value):
    """
    Mengembalikan badge HTML untuk status BOD dengan klasifikasi lebih rinci
    """
    bod_value = _safe_float_conversion(value)
    if bod_value is None:
        return mark_safe('<span class="badge bg-secondary">-</span>')
    
    if bod_value <= 2:
        return mark_safe('<span class="badge bg-success" title="BOD Rendah">Baik</span>')
    elif 2 < bod_value <= 6:
        return mark_safe('<span class="badge bg-info" title="BOD Sedang">Cukup</span>')
    elif 6 < bod_value <= 12:
        return mark_safe('<span class="badge bg-warning" title="BOD Tinggi">Sedang</span>')
    elif 12 < bod_value <= 30:
        return mark_safe('<span class="badge bg-danger" title="BOD Sangat Tinggi">Buruk</span>')
    else:
        return mark_safe('<span class="badge bg-dark" title="BOD Ekstrim">Sangat Buruk</span>')

@register.filter(name='get_cod_status')
def get_cod_status(value):
    """
    Mengembalikan badge HTML untuk status COD dengan penambahan tooltip
    """
    cod_value = _safe_float_conversion(value)
    if cod_value is None:
        return mark_safe('<span class="badge bg-secondary">-</span>')
    
    if cod_value <= 10:
        return mark_safe('<span class="badge bg-success" title="COD Rendah">Baik</span>')
    elif 10 < cod_value <= 25:
        return mark_safe('<span class="badge bg-info" title="COD Sedang">Cukup</span>')
    elif 25 < cod_value <= 50:
        return mark_safe('<span class="badge bg-warning" title="COD Tinggi">Sedang</span>')
    elif 50 < cod_value <= 100:
        return mark_safe('<span class="badge bg-danger" title="COD Sangat Tinggi">Buruk</span>')
    else:
        return mark_safe('<span class="badge bg-dark" title="COD Ekstrim">Sangat Buruk</span>')

@register.filter(name='get_tc_status')
def get_tc_status(value):
    """
    Mengembalikan badge HTML untuk status Total Coliform dengan standar WHO
    """
    tc_value = _safe_float_conversion(value)
    if tc_value is None:
        return mark_safe('<span class="badge bg-secondary">-</span>')
    
    if tc_value <= 1000:
        return mark_safe('<span class="badge bg-success" title="Memenuhi Standar WHO">Baik</span>')
    elif 1000 < tc_value <= 5000:
        return mark_safe('<span class="badge bg-info" title="Melebihi Batas Minimal">Cukup</span>')
    elif 5000 < tc_value <= 10000:
        return mark_safe('<span class="badge bg-warning" title="Tidak Aman untuk Konsumsi">Sedang</span>')
    elif 10000 < tc_value <= 50000:
        return mark_safe('<span class="badge bg-danger" title="Kontaminasi Tinggi">Buruk</span>')
    else:
        return mark_safe('<span class="badge bg-dark" title="Kontaminasi Sangat Tinggi">Sangat Buruk</span>')

## ====================== FILTER TAMBAHAN ====================== ##

@register.filter(name='water_quality_icon')
def water_quality_icon(category):
    """
    Mengembalikan ikon Font Awesome berdasarkan kategori kualitas air
    """
    category = str(category).strip().lower() if category else None
    icon_map = {
        'excellent': 'fa-check-circle',
        'baik sekali': 'fa-check-circle',
        'good': 'fa-thumbs-up',
        'baik': 'fa-thumbs-up',
        'fair': 'fa-exclamation-triangle',
        'sedang': 'fa-exclamation-triangle',
        'poor': 'fa-times-circle',
        'buruk': 'fa-times-circle',
        'sangat buruk': 'fa-skull-crossbones'
    }
    icon_class = icon_map.get(category, 'fa-question-circle')
    return mark_safe(f'<i class="fas {icon_class}"></i>')

@register.filter
def wqi_status_class(wqi):
    try:
        wqi = float(wqi)
        if wqi >= 90: return 'bg-success'
        if wqi >= 70: return 'bg-primary'
        if wqi >= 50: return 'bg-warning'
        if wqi >= 25: return 'bg-danger'
        return 'bg-dark'
    except (ValueError, TypeError):
        return 'bg-secondary'