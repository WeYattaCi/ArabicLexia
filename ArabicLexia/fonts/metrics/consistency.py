# fonts/metrics/consistency.py
from .utils import calculate_mean, calculate_std_dev

def calculate_consistency_metrics(analyzer):
    results = {}
    raw_data = analyzer.raw_data
    
    def consistency(arr):
        mean_val = calculate_mean(arr)
        if mean_val != 0:
            return calculate_std_dev(arr) / abs(mean_val)
        return None
    
    mean_width = calculate_mean(raw_data['widths'])
    if mean_width > 0:
        results['width_consistency'] = calculate_std_dev(raw_data['widths']) / mean_width
        all_bearings = raw_data['lsbs'] + raw_data['rsbs']
        results['sidebearing_consistency'] = calculate_std_dev(all_bearings) / mean_width
    
    # تم نقل معايير الاتساق العمودي إلى ملفها الخاص
    # results['balance_consistency'] is now in vertical_consistency.py
    
    results['isolated_consistency'] = consistency(raw_data['arabic_widths'])
    results['initial_consistency'] = consistency(raw_data['initial_widths'])
    results['medial_consistency'] = consistency(raw_data['medial_widths'])
    results['final_consistency'] = consistency(raw_data['final_widths'])
    
    return results