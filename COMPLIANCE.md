# Sting Operation AI Compliance & Regulatory Framework Guide

This document maps the **Sting Operation AI** wasp detection and beehive protection system to relevant New Zealand biosecurity, environmental, and data sovereignty regulations.

---

## 1. Biosecurity Act 1993 & Surveillance Protocols

Invasive wasps (German Wasp - *Vespula germanica*, Common Wasp - *Vespula vulgaris*) and potential biosecurity threats like the Yellow-legged Hornet (*Vespa velutina*) represent significant threats to New Zealand's honeybee populations and native forest ecosystems.

* **Incursion Detection:** Sting Operation AI uses class remapping (Bee=0, Wasp=1, Hornet=2) to identify invasive wasps. The system serves as an early-warning biosecurity sentinel.
* **MPI Integration & Reporting:** When the system registers high-confidence hornet or unwanted organism counts, logs can be automatically compiled into standard JSON/CSV files for submission to the **Ministry for Primary Industries (MPI)**.
* **Permitted Target Control:** Restricts active targeting systems (such as physical relays or deterrents) to verified pests, fully protecting beneficial insects (Apis mellifera).

---

## 2. Animal Welfare Act 1999

The Animal Welfare Act requires humane eradication methods for pests and provides protection for managed honeybees:
* **Non-Target Safety:** The YOLOv8 model's oriented bounding boxes (OBB) and high precision (Honeybee mAP50 ~100%) prevent active deterrent systems from triggering when honeybees are entering or exiting the hive.
* **Humane Pest Control:** Deterrents and grid zappers are calibrated to deliver instant, high-energy pulses to eliminate targeted wasps immediately, avoiding unnecessary pain or distress.

---

## 3. Māori Data Sovereignty (Te Mana Raraunga)

* **Biosecurity Data Rights:** Apiaries situated on Māori land or managed by iwi trusts yield telemetry that maps local honey production, biodiversity health, and land coordinates.
* **On-Premise Integrity:** Model inference and video streams are processed directly on-device using a Raspberry Pi 5 + Hailo NPU. Telemetry logs and camera frames are not uploaded to external cloud services, retaining data rights with iwi land trusts.
