import sqlite3
import os
from datetime import datetime
import random

class CourseManagementSystem:

    #Load .db file
    def __init__(self, db_name="school_system.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.setup_database()

    #Create table: Students, Courses, Course_Select
    def setup_database(self):
        """Creates tables using TEXT IDs to allow for leading zeros (001)."""
        """Creates tables with an is_active flag for soft deletes."""
        self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                student_name TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS courses (
                course_id TEXT PRIMARY KEY,
                university TEXT NOT NULL,
                course_year INTEGER NOT NULL,
                course_month INTEGER NOT NULL,
                course_name TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS course_select (
                student_id TEXT,
                course_id TEXT,
                PRIMARY KEY (student_id, course_id),
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
            );
        ''')
        self.conn.commit()

    # --- ID GENERATORS ---
    def generate_student_id(self):
        """Generates YYYYMM + 3-digit sequence (e.g., 202603001)"""
        now = datetime.now()
        prefix = f"{now.year}{now.month:02d}"

        self.cursor.execute("SELECT MAX(student_id) FROM students WHERE student_id LIKE ?", (f"{prefix}%",))
        last_id = self.cursor.fetchone()[0]

        if last_id:
            sequence = int(last_id[-3:]) + 1
        else:
            sequence = 1

        return f"{prefix}{sequence:03d}"

    def generate_course_id(self):
        """Generates a 3-digit sequence (e.g., 001)"""
        self.cursor.execute("SELECT MAX(course_id) FROM courses")
        last_id = self.cursor.fetchone()[0]

        if last_id:
            sequence = int(last_id) + 1
        else:
            sequence = 1

        return f"{sequence:03d}"

    # --- SETUP & SEEDING ---
    def reset_database(self):
        """Drops all tables and starts fresh."""
        self.cursor.executescript('''
            DROP TABLE IF EXISTS course_select;
            DROP TABLE IF EXISTS students;
            DROP TABLE IF EXISTS courses;
        ''')
        self.conn.commit()
        self.setup_database()
        print("\n[!] 資料庫已重設。所有舊的資料已清除。")

    def seed_random_data(self):
        print("\n[!] 正在清除舊資料並寫入新的測試資料...")
        self.reset_database()

        # Localized Taiwanese test data
        names = ["王小明", "陳小華", "林美玲", "張建國", "李雅婷", "黃志明", "吳怡君", "劉冠宇", "蔡依林", "楊宗緯"]
        subjects = ["機器學習", "神經網路", "AI 倫理", "資料科學", "機器人學"]
        universities = ["科技大學", "環球大學", "資訊學院"]

        # Create 10 Students
        student_ids = []
        for name in names:
            s_id = self.generate_student_id()
            self.cursor.execute("INSERT INTO students (student_id, student_name) VALUES (?, ?)", (s_id, name))
            student_ids.append(s_id)

        # Create 5 Courses
        course_ids = []
        for i in range(5):
            c_id = self.generate_course_id()
            self.cursor.execute("INSERT INTO courses (course_id, university, course_year, course_month, course_name) VALUES (?, ?, ?, ?, ?)",
                               (c_id, random.choice(universities), 2026, random.randint(1, 12), subjects[i]))
            course_ids.append(c_id)

        # Randomly enroll each student in 2 distinct courses
        for s_id in student_ids:
            chosen_courses = random.sample(course_ids, 2)
            for c_id in chosen_courses:
                self.cursor.execute("INSERT INTO course_select VALUES (?, ?)", (s_id, c_id))

        self.conn.commit()
        print("[+] 資料寫入完成！已建立 10 名學生，且每位學生已隨機選修 2 門課程。")
        self.display_students()
        self.display_courses()

    # --- DISPLAY TOOLS ---
    # English to Chines display adjustment
    def _pad(self, text, width):
        """Calculates visual width (Chinese=2, English=1) and adds correct spaces."""
        text = str(text)
        # If the character code is > 127, it's a full-width character (like Chinese)
        display_width = sum(2 if ord(c) > 127 else 1 for c in text)
        return text + " " * max(0, width - display_width)

    def display_students(self):
        print(f"\n{'[ 學生列表 ]':^30}")
        # Use the helper function for the header
        header = f"{self._pad('學號', 15)} | 姓名"
        print(header)
        print("-" * 30)
        self.cursor.execute("SELECT * FROM students WHERE is_active = 1")
        for row in self.cursor.fetchall():
            # Use the helper function for the data rows
            line = f"{self._pad(row[0], 15)} | {row[1]}"
            print(line)

    def display_courses(self):
        print(f"\n{'[ 課程列表 ]':^70}")
        # Use the helper function to format the header
        header = f"{self._pad('課程代碼', 10)} | {self._pad('大學', 20)} | {self._pad('年份', 6)} | {self._pad('月份', 6)} | 課程名稱"
        print(header)
        print("-" * 70)
        self.cursor.execute("SELECT * FROM courses WHERE is_active = 1")
        for row in self.cursor.fetchall():
            # Use the helper function to format each row of data
            line = f"{self._pad(row[0], 10)} | {self._pad(row[1], 20)} | {self._pad(row[2], 6)} | {self._pad(row[3], 6)} | {row[4]}"
            print(line)

    def display_enrollment_table(self, records, title):
        print(f"\n--- {title} ---")
        if not records:
            print("找不到選課紀錄。")
            return
        # Use the helper function for the header
        header = f"{self._pad('學號', 15)} | {self._pad('學生姓名', 15)} | {self._pad('課程代碼', 10)} | 課程名稱"
        print(header)
        print("-" * 75)
        for row in records:
            # Use the helper function for the data rows
            line = f"{self._pad(row[0], 15)} | {self._pad(row[1], 15)} | {self._pad(row[2], 10)} | {row[3]}"
            print(line)

    # --- DEBUG TOOLS ---
    def debug_delete_student(self, s_id):
        """Soft deletes a student by setting is_active to 0."""
        self.cursor.execute("UPDATE students SET is_active = 0 WHERE student_id = ?", (s_id,))
        self.conn.commit()
        print(f"\n[!] 測試：已停用學生 {s_id} (軟刪除)。")
        self.display_students()

    def debug_delete_course(self, c_id):
        """Soft deletes a course by setting is_active to 0."""
        self.cursor.execute("UPDATE courses SET is_active = 0 WHERE course_id = ?", (c_id,))
        self.conn.commit()
        print(f"\n[!] 測試：已停用課程 {c_id} (軟刪除)。")
        self.display_courses()

    # --- CORE FUNCTIONS ---
    def add_student(self, name):
        s_id = self.generate_student_id()
        self.cursor.execute("INSERT INTO students (student_id, student_name) VALUES (?, ?)", (s_id, name))
        self.conn.commit()
        self.display_students()

    def add_course(self, uni, year, month, name):
        c_id = self.generate_course_id()
        self.cursor.execute("INSERT INTO courses (course_id, university, course_year, course_month, course_name) VALUES (?, ?, ?, ?, ?)", (c_id, uni, year, month, name))
        self.conn.commit()
        self.display_courses()

    def enroll_student(self, s_id, c_id):
        # 1. Check if student is active
        self.cursor.execute("SELECT is_active FROM students WHERE student_id = ?", (s_id,))
        s_status = self.cursor.fetchone()

        # 2. Check if course is active
        self.cursor.execute("SELECT is_active FROM courses WHERE course_id = ?", (c_id,))
        c_status = self.cursor.fetchone()

        # 3. Block if either is missing or hidden
        if not s_status or s_status[0] == 0:
            print(f"錯誤：學生 {s_id} 不存在或已停用。")
            return

        if not c_status or c_status[0] == 0:
            print(f"錯誤：課程 {c_id} 不存在或已停用。")
            return

        # 4. Proceed with enrollment if both are active
        try:
            self.cursor.execute("INSERT INTO course_select VALUES (?, ?)", (s_id, c_id))
            self.conn.commit()
            print("選課成功！")
        except sqlite3.Error:
            print("錯誤：請檢查 ID 是否正確，或該學生已選修此課程。")

    def query_by_student(self, s_id):
        query = """
            SELECT s.student_id, s.student_name, c.course_id, c.course_name
            FROM course_select cs
            JOIN students s ON cs.student_id = s.student_id
            JOIN courses c ON cs.course_id = c.course_id
            WHERE cs.student_id = ? AND s.is_active = 1
        """ # REMOVED: AND c.is_active = 1
        self.cursor.execute(query, (s_id,))
        results = self.cursor.fetchall()
        self.display_enrollment_table(results, f"學生 {s_id} 的選課紀錄")

    def query_by_course(self, c_id):
        query = """
            SELECT s.student_id, s.student_name, c.course_id, c.course_name
            FROM course_select cs
            JOIN students s ON cs.student_id = s.student_id
            JOIN courses c ON cs.course_id = c.course_id
            WHERE cs.course_id = ? AND s.is_active = 1
        """ # REMOVED: AND c.is_active = 1
        self.cursor.execute(query, (c_id,))
        results = self.cursor.fetchall()
        self.display_enrollment_table(results, f"課程 {c_id} 的選課紀錄")

    def modify_enrollment(self, s_id, old_cid, new_cid):
        # Check if the new target course is active
        self.cursor.execute("SELECT is_active FROM courses WHERE course_id = ?", (new_cid,))
        c_status = self.cursor.fetchone()

        if not c_status or c_status[0] == 0:
            print(f"錯誤：目標課程 {new_cid} 不存在或已停用。")
            return

        self.cursor.execute("UPDATE course_select SET course_id = ? WHERE student_id = ? AND course_id = ?", (new_cid, s_id, old_cid))
        self.conn.commit()
        print("選課修改成功。")
        self.query_by_student(s_id)

    def delete_enrollment(self, s_id, c_id):
        self.cursor.execute("DELETE FROM course_select WHERE student_id = ? AND course_id = ?", (s_id, c_id))
        self.conn.commit()
        print(f"已成功退選。學生：{s_id}，課程：{c_id}。")
        self.query_by_student(s_id)


# --- CLI LOOP ---
def run_cli():
    cms = CourseManagementSystem()
    while True:
        print("\n" + "="*45)
        print("大學校務管理系統")
        print("備註：[0]-重設資料庫 [s]-產生測試資料")
        print("備註：[ds]-刪除學生  [dc]-刪除課程")
        print("="*45)
        print("1. 新增學生")
        print("2. 新增課程")
        print("3. 學生選課")
        print("4. 依學號查詢")
        print("5. 依課程代碼查詢")
        print("6. 修改選課")
        print("7. 退選課程")
        print("8. 離開系統")

        choice = input("\n請輸入選項：").lower() # .lower() handles 'S' or 's'

        if choice == '0':
            confirm = input("您確定嗎？這將會刪除所有資料 (y/n)：")
            if confirm.lower() == 'y': cms.reset_database()
        elif choice == 's':
            cms.seed_random_data()
        elif choice == '1':
            cms.add_student(input("姓名："))
        elif choice == '2':
            cms.add_course(input("大學："), input("年份："), input("月份："), input("課程名稱："))
        elif choice == '3':
            cms.enroll_student(input("學號："), input("課程代碼："))
        elif choice == '4':
            cms.query_by_student(input("學號："))
        elif choice == '5':
            cms.query_by_course(input("課程代碼："))
        elif choice == '6':
            cms.modify_enrollment(input("學號："), input("原課程代碼："), input("新課程代碼："))
        elif choice == '7':
            cms.delete_enrollment(input("學號："), input("課程代碼："))
        elif choice == 'ds':
            cms.debug_delete_student(input("請輸入要刪除的學號："))
        elif choice == 'dc':
            cms.debug_delete_course(input("請輸入要刪除的課程代碼："))
        elif choice == '8':
            break

if __name__ == "__main__":
    run_cli()