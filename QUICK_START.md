# 🚀 QUICK START GUIDE

## Which Version Should I Use?

### Option 1: Full Version (result_processor.py)
**Use if you have MySQL installed**
- ✅ Full database integration
- ✅ Store data permanently in MySQL
- ✅ Query historical results
- ⚠️ Requires MySQL setup

### Option 2: Lite Version (result_processor_lite.py) ⭐ RECOMMENDED FOR BEGINNERS
**Use if you want quick testing**
- ✅ No database needed
- ✅ All report generation features
- ✅ Easier to get started
- ⚠️ No permanent data storage

## 📦 Installation (Both Versions)

1. **Install Python packages**:
```bash
pip install pandas numpy openpyxl reportlab
```

For full version only:
```bash
pip install mysql-connector-python
```

Or install everything at once:
```bash
pip install -r requirements.txt
```

## ▶️ Running the Application

### Lite Version (Easiest):
```bash
python result_processor_lite.py
```

### Full Version (With MySQL):
```bash
python result_processor.py
```

## 📝 Step-by-Step Usage

1. **Load Data**
   - Click "Load CSV File"
   - Select `student_marks__1_.csv`
   - Preview appears at bottom

2. **Database** (Full version only)
   - Enter MySQL credentials
   - Click "Connect to Database"
   - Click "Save to Database"

3. **Process Results**
   - Click "Process Data"
   - Wait for confirmation
   - View processed data in preview

4. **Generate Reports**
   - Click any report button:
     - 📑 Excel Report: Complete workbook
     - 📄 PDF Report: Summary report
     - 📋 Individual Cards: One PDF per student

## 📂 Where Are My Files?

All outputs are saved in: `/mnt/user-data/outputs/`

- Excel: `result_report_TIMESTAMP.xlsx`
- PDF Summary: `result_summary_TIMESTAMP.pdf`
- Report Cards: `individual_reports/` folder

## 🆘 Troubleshooting

**"Module not found"**
→ Run: `pip install -r requirements.txt`

**"Database connection failed"** (Full version)
→ Check MySQL is running
→ Verify your password is correct
→ Try the Lite version instead!

**"Permission denied"**
→ Check folder permissions
→ Try running as administrator

## 💡 Tips

- Use **Lite version** for quick testing and demos
- Use **Full version** for production/permanent storage
- CSV must have: Student_ID, Student_Name, Subject, Marks
- Passing grade is 40%
- Maximum marks per subject is 100

## 📊 What Gets Calculated?

- ✅ Total marks per student
- ✅ Percentage score
- ✅ Letter grade (A+ to F)
- ✅ Pass/Fail status
- ✅ Class ranking
- ✅ Subject-wise analysis

## 🎯 Ready to Start?

1. Open terminal/command prompt
2. Navigate to project folder
3. Run: `python result_processor_lite.py`
4. Load your CSV file
5. Click "Process Data"
6. Generate reports!

That's it! You're ready to go! 🎉
