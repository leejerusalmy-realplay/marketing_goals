*Lee Jerusalmy*

# Playbook — RealPrize + LoneStar

How to understand and re-run marketing goals for **both brands** (shared pipeline; brand knobs differ).

---

## File roles (what each file is for)

### 1. Entry / agent transfer

| File | Purpose | When you open it |
|------|---------|------------------|
| **`HANDOFF.md`** | **האנדוף הראשי.** סטטוס, מה כבר נעול, מה הצעד הבא, כללי עבודה. | **כל צ'אט סוכן חדש** — קודם כל |
| **`handoffs/`** | האנדופים **נושאיים** (ניסוי CV, …). לא מחליפים את הראשי. | רק כשעובדים על אותו נושא |
| **`FOLDER_HYGIENE.md`** | כללי ניקיון Drive + git | לפני יצירת תיקיות/קבצים חדשים |

### 2. “איך זה עובד” (methodology)

| File | Purpose | Level |
|------|---------|--------|
| **`METHODOLOGY.md`** | מה אנחנו מחשבים + **מה משותף / מה שונה** בין RP ל-LS (תמצית). | קצר — first orientation |
| **`PIPELINE_FLOW.md`** | **כל שלב בצינור** (boxes): patch → winsor → CV → curve → organic → goals, עם דוגמאות. | מלא — “איך זה רץ” |
| **`CONFIG_AND_KNOBS.md`** | **כל הכפתורים** (as_of, patches, trim_config, CV, min_cohort_dates, scope…). איפה בקוד וב-yaml. | מפת knobs |
| **`TRIM_BY_POPULATION.md`** | רק trim/winsor **לפי population** (Web 1% vs 0%…). חיתוך מ-CONFIG. | cheat sheet winsor |
| **`WORKED_EXAMPLE_RP_WEB.md`** | **דוגמת מספרים צעצועית** (RP Web) לעשות חשבון ביד. לא run אמיתי. | כשאת רוצה לראות נוסחאות במספרים |

### 3. תפעול / היסטוריה

| File | Purpose |
|------|---------|
| **`NOTEBOOK_INTEGRATION.md`** | איך סוכן + את + Colab + `runs/` עובדים יחד (לא מתודולוגיה). |
| **`DECISIONS.md`** | **יומן החלטות** מתוארך — מה ננעל מתי. לא הסבר של הפייפליין. |
| **`sql_steps/`** | שאילתות Excel-check (בדרך כלל RP fixtures; math משותף). |
| **`examples/`** | CSVs לדוגמה (צורת עמודות). |

### Google Doc
Plain-language twin (קריאה רגועה):  
https://docs.google.com/document/d/1rTx9-CdjUaaOESO6D0kRY-xtJ5TkwwIbG1Ia3ObzMns/edit

---

## למה לא מאחדים הכול לקובץ אחד?

| צורך | קובץ |
|------|------|
| “מה קורה אחרי הקלקה בסוכן חדש?” | HANDOFF |
| “איך בונים goal מספרית?” | PIPELINE + WORKED_EXAMPLE |
| “איזה % winsor ל-Web ב-LS?” | CONFIG / TRIM |
| “מה החלטנו ב-30.7?” | DECISIONS |
| “איך לשתף run עם הסוכן?” | NOTEBOOK_INTEGRATION |

אותו ידע מופיע בכמה מקומות **בקצרה**, עם קישור למקור המלא — כדי לא לאבד הכוון.

---

## Learning order

1. `HANDOFF.md`
2. `METHODOLOGY.md` או `CONFIG_AND_KNOBS.md` (shared vs different)
3. `PIPELINE_FLOW.md`
4. אופציונלי: `WORKED_EXAMPLE_RP_WEB.md`
5. `sql_steps/` ל-Excel
6. `handoffs/<topic>.md` רק לנושאים ממוקדים

## Verification rule

Explain → SQL in `sql_steps/` → Excel → רק אז נעולים.
