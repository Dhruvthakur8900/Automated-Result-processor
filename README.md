# 📊 Automated Result Processing & Report Generator

A comprehensive Python application for processing student results, managing data in MySQL, and generating professional reports.

## 🎯 Features

- **CSV Data Import**: Load student marks from CSV files
- **Data Processing**: Automatic calculation of totals, percentages, grades, and rankings
- **MySQL Integration**: Store and retrieve results from database
- **Multiple Report Formats**:
  - Excel reports with multiple sheets (Summary, Detailed Marks, Statistics)
  - PDF summary reports with formatted tables
  - Individual student report cards in PDF format
- **User-Friendly GUI**: Built with Tkinter for easy interaction

## 📋 Requirements

- Python 3.8+
- MySQL Server (installed and running)
- Required Python packages (see requirements.txt)

## 🚀 Installation

1. **Install Python packages**:
```bash
pip install -r requirements.txt
```

2. **Install MySQL Server** (if not already installed):
   - **Windows**: Download from https://dev.mysql.com/downloads/mysql/
   - **Linux**: `sudo apt-get install mysql-server`
   - **Mac**: `brew install mysql`

3. **Start MySQL Service**:
   - **Windows**: MySQL service should auto-start
   - **Linux**: `sudo service mysql start`
   - **Mac**: `brew services start mysql`

## 💻 Usage

1. **Run the application**:
```bash
python result_processor.py
```

2. **Follow the workflow**:

   **Step 1: Load Data**
   - Click "📂 Load CSV File"
   - Select your CSV file (e.g., student_marks__1_.csv)
   - Data preview will appear at the bottom

   **Step 2: Database Configuration**
   - Enter your MySQL credentials (default: host=localhost, user=root)
   - Click "🔗 Connect to Database" to establish connection
   - Click "💾 Save to Database" to store raw data

   **Step 3: Process Results**
   - Click "⚙️ Process Data"
   - The system will calculate:
     - Total marks and percentage
     - Grades (A+, A, B, C, D, F)
     - Pass/Fail status (40% passing threshold)
     - Class ranking

   **Step 4: Generate Reports**
   - **📑 Excel Report**: Comprehensive workbook with summary, details, and statistics
   - **📄 PDF Summary**: Overall class performance report
   - **📋 Individual Reports**: Separate PDF report card for each student

## 📊 Grading System

| Percentage | Grade |
|-----------|-------|
| 90-100%   | A+    |
| 80-89%    | A     |
| 70-79%    | B     |
| 60-69%    | C     |
| 50-59%    | D     |
| Below 50% | F     |

**Pass Mark**: 40% overall percentage

## 📁 Output Files

All generated reports are saved in `/mnt/user-data/outputs/`:
- Excel reports: `result_report_TIMESTAMP.xlsx`
- PDF summaries: `result_summary_TIMESTAMP.pdf`
- Individual reports: `individual_reports/report_card_ID_NAME.pdf`

## 🗄️ Database Structure

### Tables Created:

1. **student_marks**: Raw student data
   - Student_ID, Student_Name, Subject, Marks

2. **processed_results**: Computed results
   - Student_ID, Student_Name, Total_Marks, Percentage, Grade, Result

## 🎨 CSV File Format

Your CSV should have these columns:
```
Student_ID,Student_Name,Subject,Marks
1,Aditya Agarwal,Maths,51
1,Aditya Agarwal,Science,31
...
```

## 🔧 Troubleshooting

**Database Connection Failed**:
- Check if MySQL service is running
- Verify credentials (username/password)
- Ensure database user has CREATE/INSERT permissions

**Module Not Found**:
- Run: `pip install -r requirements.txt`

**Permission Denied for Output Files**:
- Check write permissions for `/mnt/user-data/outputs/` directory

## 📝 Notes

- Maximum marks per subject is assumed to be 100
- Minimum passing marks per subject is 40
- Overall pass percentage is 40%
- Rank is based on overall percentage (higher percentage = better rank)

## 🤝 Support

For issues or questions, please check:
- MySQL installation documentation
- Python package documentation (pandas, reportlab, openpyxl)

## 📄 License

This project is created for educational purposes.
