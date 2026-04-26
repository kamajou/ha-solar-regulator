# Solar Regulator – Home Assistant Custom Integration

Automatische Nulleinspeisung für Balkonkraftwerke. Der Regler passt das Wechselrichter-Limit dynamisch an den aktuellen Hausverbrauch an, sodass kein Strom ins Netz eingespeist wird.

---

## Funktionsweise

```
[Verbrauchssensor 1]  ┐
[Verbrauchssensor 2]  ├──→  Solar Regulator  ──→  WR-Limit Entity (%)
[Verbrauchssensor …]  ┘         ↑
                          [Panelleistung]
                          [Batterie-SOC]
                          [Solar-Forecast]
```

Der Regler summiert alle konfigurierten Verbrauchssensoren und setzt das Wechselrichter-Limit entsprechend. Verschiedene Optimierungsmodi greifen je nach Batterie-Ladestand und Panelleistung.

### Regelungsmodi

| Modus | Bedingung | Verhalten |
|---|---|---|
| **Normal** | Standardbetrieb | Sollwert = Gesamtverbrauch |
| **Batterie voll · Panel-Formel** | Akku voll + Sonne scheint | Sollwert aus Panelleistung abgeleitet (200W-Stufen) |
| **Batterie voll · Verbrauch + Marge** | Akku voll, kein Panel | Sollwert = Verbrauch + konfigurierbare Marge |
| **Deaktiviert** | Schalter aus | Sollwert = Minimalleistung |

### Spike-Filter

Plötzliche Lastspitzen (z. B. Anlaufstrom) werden zeitbasiert gefiltert: Ein Sprung über der konfigurierten Schwelle wird erst akzeptiert, wenn er länger als die eingestellte Bestätigungszeit anhält.

### Ausgabe-Entscheidung

Der Sollwert wird nur ausgegeben wenn:
- der Verbrauch so stark gesunken ist, dass die erlaubte Einspeisung überschritten würde (sofortige Reaktion), **oder**
- die Änderung größer als der konfigurierte Mindestabstand ist.

---

## Installation

### Via HACS (empfohlen)

1. HACS öffnen → **Custom repositories**
2. URL eingeben: `https://github.com/kamajou/ha-solar-regulator`
3. Kategorie: **Integration** → **Add**
4. Solar Regulator installieren
5. Home Assistant neu starten

### Manuell

1. Ordner `custom_components/solar_regulator/` in dein HA-Konfigurationsverzeichnis kopieren
2. Home Assistant neu starten

---

## Einrichtung

1. **Einstellungen → Integrationen → + Hinzufügen → Solar Regulator**
2. Pflichtfelder konfigurieren:
   - **Verbrauchssensoren** – beliebig viele Leistungssensoren (W)
   - **WR-Limit Entity** – die `number`-Entity des Wechselrichters (erwartet 0–100%)
3. Optionale Felder nach Bedarf setzen

---

## Konfigurationsparameter

### Pflicht

| Parameter | Beschreibung |
|---|---|
| Verbrauchssensoren | Liste von Leistungssensoren (W), beliebig viele |
| WR-Limit Entity | Wechselrichter-Limit Entity (number, 0–100%) |

### Regelung

| Parameter | Standard | Beschreibung |
|---|---|---|
| Max. WR-Leistung | 800 W | Physikalisches Maximum des Wechselrichters |
| Min. WR-Leistung | 10 W | Untergrenze des Sollwerts |
| Regelintervall | 30 s | Wie oft der Regler läuft |
| Mindestabstand | 20 W | Minimale Änderung für eine Sollwert-Ausgabe |
| Grundverbrauch | 0 W | Fixer Offset, wird zum Verbrauch addiert |
| Erlaubte Einspeisung | 0 W | Toleranz bevor sofort reagiert wird |

### Spike-Filter

| Parameter | Standard | Beschreibung |
|---|---|---|
| Spike-Schwelle | 500 W | Max. erlaubter Anstieg pro Sensor pro Zyklus |
| Bestätigungszeit | 60 s | Wie lange ein Spike anhalten muss um akzeptiert zu werden |

### Batterieoptimierung (optional)

| Parameter | Standard | Beschreibung |
|---|---|---|
| Batterie-SOC Sensor | – | Sensor für den Akku-Ladestand (%) |
| Akku-Vollschwelle | 90 % | Ab diesem SOC greift die Optimierung |
| Marge (Akku voll) | 20 % | Aufschlag auf Verbrauch wenn Akku voll und kein Panel |
| Panelleistung Sensor | – | Aktuell erzeugte Leistung der Panels (W) |
| Solar-Forecast Sensor | – | Produktionsvorhersage für morgen |

---

## HA-Entities

Die Integration erstellt folgende Entities:

| Entity | Typ | Beschreibung |
|---|---|---|
| `Solar Regulator` | Schalter | Regler ein/aus. Zustand bleibt nach Neustart erhalten. |
| `Solar Regulator Gesamtverbrauch` | Sensor | Summe aller Eingangssensoren + Grundverbrauch (W) |
| `Solar Regulator Sollwert` | Sensor | Zuletzt gesetztes WR-Limit (`x W (y%)`) |
| `Solar Regulator Modus` | Sensor | Aktiver Regelungsmodus |
| `Solar Regulator Status` | Sensor | Betriebsstatus und Warnungen |

---

## Voraussetzungen

- Home Assistant 2024.1 oder neuer
- Wechselrichter-Limit als `number`-Entity in HA verfügbar (z. B. via OpenDTU)
- Mindestens ein Leistungssensor in HA verfügbar
