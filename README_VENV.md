# Python 3.11 Virtual Environment Setup

## סקירה כללית
הסביבה הוירטואלית נוצרה בהצלחה עם Python 3.11.9 עבור פרויקט TradingApp.

## מיקום הסביבה הוירטואלית
```
venv_py311/
├── Scripts/          # קבצי הפעלה (Windows)
├── Lib/              # חבילות Python
├── Include/          # קבצי header
└── pyvenv.cfg        # תצורת הסביבה
```

## הפעלת הסביבה הוירטואלית

### PowerShell (מומלץ)
```powershell
.\venv_py311\Scripts\Activate.ps1
```

### Command Prompt
```cmd
venv_py311\Scripts\activate.bat
```

### ישירות
```powershell
& "venv_py311\Scripts\Activate.ps1"
```

## בדיקה שהסביבה פעילה
כאשר הסביבה פעילה, תראה `(venv_py311)` בתחילת שורת הפקודה:
```powershell
(venv_py311) PS D:\Investment Codes\TradingApp>
```

## בדיקת גרסת Python
```powershell
python --version
# אמור להציג: Python 3.11.9
```

## בדיקת מיקום Python
```powershell
Get-Command python
# אמור להציג את הנתיב: D:\Investment Codes\TradingApp\venv_py311\Scripts\python.exe
```

## התקנת חבילות
```powershell
# עדכון pip
python -m pip install --upgrade pip

# התקנת חבילה
python -m pip install package_name

# התקנה מקובץ requirements
python -m pip install -r requirements_py311.txt
```

## יציאה מהסביבה הוירטואלית
```powershell
deactivate
```

## חבילות מותקנות
- Python 3.11.9
- pip 25.2
- pandas 2.3.1 (דוגמה)

## פתרון בעיות

### אם הסביבה לא מופעלת
1. ודא שאתה בתיקיית הפרויקט
2. בדוק שהתיקייה `venv_py311` קיימת
3. נסה להפעיל עם הנתיב המלא

### אם pip לא עובד
השתמש ב:
```powershell
python -m pip install package_name
```

### אם יש בעיות הרשאה
הפעל PowerShell כמנהל מערכת או השתמש ב:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## הערות חשובות
- תמיד הפעל את הסביבה הוירטואלית לפני עבודה על הפרויקט
- השתמש ב-`python -m pip` במקום `pip` ישירות
- הסביבה הוירטואלית מבודדת מהמערכת הראשית
- כל החבילות יותקנו בתוך `venv_py311/Lib/site-packages/`
