# Changelog

## [1.0.1] – 2026-04-26

### Added
- Integration-Icon (`icon.svg`) — wird in HA Integrationsübersicht und HACS angezeigt

---

## [1.0.0] – 2026-04-25

### Initial Release

#### Regelung
- Sollwert wird aus der Summe beliebig vieler konfigurierbarer Verbrauchssensoren berechnet
- Ausgabe-Entity erwartet Prozent (0–100%) — interne Berechnung in Watt mit automatischer Konvertierung
- Konfigurierbarer Grundverbrauch (fixer Offset, wird zur Sensor-Summe addiert)
- Konfigurierbarer Mindestabstand: Sollwert wird nur ausgegeben wenn die Änderung groß genug ist
- Erlaubte Einspeisung: konfigurierbare Toleranz bevor sofort auf sinkenden Verbrauch reagiert wird
- Regler startet sofort beim HA-Start (kein Warten auf erstes Intervall)

#### Spike-Filter (zeitbasiert)
- Plötzliche Lastsprünge über der konfigurierten Schwelle werden zunächst ignoriert
- Erst wenn der hohe Wert länger als die konfigurierte Bestätigungszeit anhält, wird er als echte Last akzeptiert
- Verhindert Fehlreaktionen auf Anlaufströme und kurzfristige Messfehler

#### Batterieoptimierung (optional)
- **Modus „Normal"**: Sollwert = Gesamtverbrauch
- **Modus „Batterie voll · Panel-Formel"**: wenn Akku-SOC über Schwelle und Panelleistung > 0 → Sollwert aus Panelleistung abgeleitet (auf nächstes 200W-Vielfaches abrunden, 200W abziehen, min. 200W), aber nie kleiner als Gesamtverbrauch
- **Modus „Batterie voll · Verbrauch + Marge"**: wenn Akku voll aber keine Panelleistung → Sollwert = Verbrauch × (1 + Marge%)
- Konfigurierbare Akku-Vollschwelle (Standard: 90%) und Marge (Standard: 20%)

#### HA-Entities
- **Schalter** `Solar Regulator`: Regler ein/aus. Bei Aus wird sofort Minimalleistung ausgegeben. Zustand bleibt nach HA-Neustart erhalten (RestoreEntity).
- **Sensor** `Solar Regulator Gesamtverbrauch`: Summe aller Eingangssensoren + Grundverbrauch in Watt
- **Sensor** `Solar Regulator Sollwert`: Zuletzt gesetztes WR-Limit als `x W (y%)`
- **Sensor** `Solar Regulator Modus`: Aktiver Regelungsmodus
- **Sensor** `Solar Regulator Status`: Betriebsstatus — zeigt `Aktiv`, `Sensor nicht verfügbar`, `Spike gefiltert` oder `Fehler: …`
- Alle Sensoren sind `EntityCategory.DIAGNOSTIC` — keine Logbook-Einträge

#### Konfiguration
- Vollständige UI-Konfiguration via HA Config Flow und Options Flow
- Alle Parameter zur Laufzeit änderbar (Neustart der Integration, kein HA-Neustart nötig)
- Optionale Sensoren: Panelleistung, Batterie-SOC, Solar-Forecast
- Deutsche UI-Übersetzung

#### Fehlerbehandlung
- Exceptions im Regelzyklus werden abgefangen und im Status-Sensor angezeigt
- Nicht verfügbare oder nicht-numerische Sensoren werden übersprungen und im Status gemeldet
- Alle Sensoren nicht verfügbar → Status `Keine Sensoren verfügbar`

#### Deployment
- HACS-kompatibel (Custom Repository)
- GitHub Actions Workflow: automatisches Release bei Tag-Push (`*.*.*`)
