#this is main.py, the main file of the project. It is responsible for running the app and managing the screens.
# นำเข้าเครื่องมือของ Kivy ที่จำเป็นต้องใช้
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
import sys
import os
# ดึง path ของโฟลเดอร์หลัก เพื่อให้เรียกใช้ Backend ได้
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Backend.sudoku_engine import SudokuEngine

# สร้างคลาสสำหรับกระดาน Sudoku
class SudokuBoard(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 1. ตั้งค่าตาราง: บังคับให้มี 9 คอลัมน์
        self.cols = 9       
        self.spacing = 2    # ระยะห่างระหว่างช่อง
        self.padding = 10   # ระยะขอบรอบกระดาน
        
        # 2. เตรียม List ว่างๆ เอาไว้เก็บช่องตัวเลขทั้ง 81 ช่อง
        self.cells = []  

        #สร้างตัวแปรสมองของเกม
        self.engine = SudokuEngine()

        # 3. วนลูป 81 รอบ เพื่อสร้างช่องกรอกตัวเลข (TextInput)
        for i in range(81):
            cell = TextInput(
                text='',
                multiline=False,     # ไม่ให้กด Enter ขึ้นบรรทัดใหม่
                halign='center',     # จัดตัวเลขให้อยู่ตรงกลาง
                font_size=24,
                input_filter='int'   # ให้กรอกได้เฉพาะตัวเลขเท่านั้น
            )
            # นำช่องที่สร้างเสร็จไปแปะบนกระดาน และเก็บเข้า List
            self.add_widget(cell)
            self.cells.append(cell)
    def clear_board(self, instance):
        # 1. ล้างตัวเลขบนหน้าจอให้ว่างเปล่า
        for cell in self.cells:
            cell.text = ''
        # 2. ล้างข้อมูลในกระดานหลังบ้านให้เป็น 0 ทั้งหมด
        self.engine.board = [[0 for _ in range(9)] for _ in range(9)]
    def new_game(self, instance):
        # 1. ให้ Backend สร้างโจทย์ใหม่ (เริ่มต้นด้วยแบบ "Easy" ก่อน)
        board_data = self.engine.generate_board("Easy")
        
        # 2. นำตัวเลขจากโจทย์มาแสดงบนหน้าจอ
        for i in range(81):
            row = i // 9
            col = i % 9
            val = board_data[row][col]
            
            cell = self.cells[i]
            if val != 0:
                cell.text = str(val)
                # ถ้าเป็นตัวเลขโจทย์ (ล็อคไว้ไม่ให้แก้) และเปลี่ยนสีพื้นหลังให้เป็นสีเทาอ่อน
                cell.readonly = True
                cell.background_color = [0.9, 0.9, 0.9, 1] 
            else:
                cell.text = ''
                # ถ้าเป็นช่องว่าง (ให้ผู้เล่นพิมพ์ได้ปกติ) และเป็นสีขาว
                cell.readonly = False
                cell.background_color = [1, 1, 1, 1]    




# กำหนดขนาดหน้าต่างแอปเริ่มต้น
Window.size = (500, 650)

# สร้างคลาสหลักของแอปพลิเคชัน
class SudokuApp(App):
    def build(self):
        # 1. ต้องสร้าง Layout หลักขึ้นมาก่อนเป็นอันดับแรกสุดเลย
        main_layout = BoxLayout(orientation='vertical')

        self.seconds_elapsed = 0
        self.timer_event = None
        
        # 2. ค่อยสร้าง Label และนำไปแปะใส่ main_layout ที่สร้างไว้แล้ว
        self.timer_label = Label(text="Time: 00:00", font_size=24, size_hint=(1, 0.1))
        main_layout.add_widget(self.timer_label)
        
        # ส่วนที่ 1: นำกระดาน SudokuBoard ที่เราสร้างไว้มาใส่ (ให้พื้นที่ความสูง 75%)
        self.board = SudokuBoard(size_hint=(1, 0.75))
        main_layout.add_widget(self.board)
        
        # ส่วนที่ 2: พื้นที่ปุ่มควบคุมด้านล่าง (ให้พื้นที่ความสูง 15%)
        button_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.15), padding=10, spacing=10)
        
        btn_new = Button(text="New Game", font_size=20)
        btn_clear = Button(text="Clear", font_size=20)
        btn_solve = Button(text="Solve", font_size=20)
        
        #เมื่อกดปุ่ม Clear ให้ไปเรียกฟังก์ชัน clear_board
        btn_new.bind(on_press=self.board.new_game)
        btn_clear.bind(on_press=self.board.clear_board)
        
        button_layout.add_widget(btn_new)
        button_layout.add_widget(btn_clear)
        button_layout.add_widget(btn_solve)
        
        main_layout.add_widget(button_layout)

        # คำสั่ง return ต้องอยู่ตรงนี้ครับ (ย่อหน้าให้ตรงกับ main_layout บรรทัดบนๆ)
        return main_layout

    def update_timer(self, dt):
        self.seconds_elapsed += 1
        minutes = self.seconds_elapsed // 60
        seconds = self.seconds_elapsed % 60
        self.timer_label.text = f"Time: {minutes:02d}:{seconds:02d}"
    
    
# คำสั่งสำหรับเริ่มรันโปรแกรม
if __name__ == '__main__':
    SudokuApp().run()
# คำสั่งสำหรับเริ่มรันโปรแกรม
if __name__ == '__main__':
    SudokuApp().run()