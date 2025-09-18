# fonts/metrics/consistency.py
from .utils import calculate_mean, calculate_std_dev

def calculate_consistency_metrics(analyzer):
    """
    تحسب جميع معايير الاتساق للخط.
    """
    results = {}
    raw_data = analyzer.raw_data

    def consistency_score(data_list):
        mean = calculate_mean(data_list)
        return (calculate_std_dev(data_list) / mean) if mean and mean > 0 else None

    # اتساق عام
    results['width_consistency'] = consistency_score(raw_data['all_widths'])
    cap_height_funits = (analyzer.metrics.get('cap_height') or 0) * analyzer.font['head'].unitsPerEm
    results['balance_consistency'] = (calculate_std_dev(raw_data['vertical_centers']) / cap_height_funits) if cap_height_funits and cap_height_funits > 0 else None
    results['sidebearing_consistency'] = consistency_score(raw_data['left_side_bearings'] + raw_data['right_side_bearings'])

    # اتساق لاتيني
    results['latin_ascender_consistency'] = consistency_score(raw_data['latin_ascenders'])
    results['latin_descender_consistency'] = consistency_score([abs(d) for d in raw_data['latin_descenders']])

    # اتساق عربي
    results['arabic_ascender_consistency'] = consistency_score(raw_data['arabic_ascenders'])
    results['arabic_descender_consistency'] = consistency_score([abs(d) for d in raw_data['arabic_descenders']])
    results['isolated_consistency'] = consistency_score(raw_data['arabic_widths'])
    results['initial_consistency'] = consistency_score(raw_data['initial_widths'])
    results['medial_consistency'] = consistency_score(raw_data['medial_widths'])
    results['final_consistency'] = consistency_score(raw_data['final_widths'])

    return results