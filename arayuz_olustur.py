"""Mevcut CSV ve raporlardan çevrimdışı sunum arayüzü üretir; analiz çalıştırmaz."""
import csv
import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent


def build():
    tables = {}
    for key, relative in [('raw', 'used_cars.csv'), ('clean', 'data/used_cars_cleaned.csv'),
                          ('features', 'data/used_cars_features.csv')]:
        with (BASE / relative).open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.reader(handle)
            tables[key] = {'columns': next(reader), 'rows': list(reader)}
    reports = {}
    for key, relative in [('eda', 'eda/EDA_RAPORU.md'), ('clean', 'cleaning/TEMIZLEME_RAPORU.md'),
                          ('features', 'features/OZELLIK_RAPORU.md'),
                          ('regression', 'regression/REGRESYON_HAZIRLIK_RAPORU.md'),
                          ('clustering', 'clustering/KUMELEME_HAZIRLIK_RAPORU.md')]:
        reports[key] = (BASE / 'reports' / relative).read_text(encoding='utf-8')
    manifests = {key: json.loads((BASE / 'data' / key / 'manifest.json').read_text(encoding='utf-8'))
                 for key in ['regression', 'clustering']}
    payload = {'tables': tables, 'reports': reports, 'manifests': manifests,
               'generated': datetime.now(timezone.utc).isoformat()}
    # HTML içindeki veri metni script etiketini kapatamaz.
    encoded = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    template = (BASE / 'arayuz' / 'sablon.html').read_text(encoding='utf-8')
    output = BASE / 'arayuz' / 'index.html'
    output.write_text(template.replace('__PROJECT_DATA__', encoded), encoding='utf-8')
    print('Arayüz hazır:', output)
    print('Tarayıcıda açın. Kaynak veri değişmedi; analiz veya model eğitimi yapılmadı.')


if __name__ == '__main__':
    build()
