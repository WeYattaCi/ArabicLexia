# fonts/metrics/consistency.py
from .utils import calculate_mean, calculate_std_dev

def calculate_consistency_metrics(analyzer):
    results = {}
    raw_data = analyzer.raw_data
    
    mean_width = calculate_mean(raw_data['widths'])
    if mean_width > 0:
        results['width_consistency'] = calculate_std_dev(raw_data['widths']) / mean_width
        all_bearings = raw_data['lsbs'] + raw_data['rsbs']
        results['sidebearing_consistency'] = calculate_std_dev(all_bearings) / mean_width

    cap_height = analyzer.metrics.get('cap_height')
    if cap_height and cap_height > 0:
        results['balance_consistency'] = calculate_std_dev(raw_data['v_centers']) / cap_height
    
    def calc_consistency(data_list):
        mean_val = calculate_mean(data_list)
        if mean_val != 0:
            return calculate_std_dev(data_list) / abs(mean_val)
        return None
    
    results['arabic_ascender_consistency'] = calc_consistency(raw_data['arabic_ascenders'])
    results['arabic_descender_consistency'] = calc_consistency(raw_data['arabic_descenders'])
    results['latin_ascender_consistency'] = calc_consistency(raw_data['latin_ascenders'])
    results['latin_descender_consistency'] = calc_consistency(raw_data['latin_descenders'])

    return results