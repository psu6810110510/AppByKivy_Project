# นำเข้าเครื่องมือของ Kivy ที่จำเป็นต้องใช้
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore 
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.togglebutton import ToggleButton # [เพิ่ม] ปุ่มแบบสวิตช์เปิด-ปิด

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Backend.sudoku_engine import SudokuEngine

class SudokuBoard(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 9       
        self.spacing = 2    
        self.padding = 10   
        self.cells = []  
        self.engine = SudokuEngine()
        self.is_generating = False 
        self.note_mode = False  # [เพิ่ม] สถานะโหมดจดโน้ต

        for i in range(81):
            cell = TextInput(
                text='',
                multiline=False,     
                halign='center',     
                font_size=26,
                input_filter='int',
                background_normal='',
                background_color=[1, 1, 1, 1]
            )
            
            cell.cell_index = i      
            cell.last_text = ''  # [เพิ่ม] เก็บค่าของช่องก่อนที่จะโดนเปลี่ยน เพื่อใช้เวลา Undo             
            cell.is_note = False  # [เพิ่ม] แยกสถานะว่าเป็นตัวเลขปกติหรือโน้ต
            cell.bind(text=self.check_answer)     
            
            self.add_widget(cell)
            self.cells.append(cell)

    def check_answer(self, instance, value):
        if self.is_generating:
            return

        app = App.get_running_app()
        row = instance.cell_index // 9
        col = instance.cell_index % 9

        # 1. ถ้าลบเลขจนว่างเปล่า
        if value == '':
            app.record_history(
                index=instance.cell_index,
                old_text=instance.last_text, new_text='',
                old_color=instance.foreground_color[:], new_color=[0.1, 0.1, 0.1, 1],
                old_readonly=instance.readonly, new_readonly=False,
                score_diff=0
            )
            self.is_generating = True
            instance.foreground_color = [0.1, 0.1, 0.1, 1]
            instance.last_text = ''
            instance.is_note = False
            instance.font_size = 26 
            self.engine.board[row][col] = 0 
            self.is_generating = False
            return

        # ตรวจสอบว่าต้องเป็นเลข 1-9 เท่านั้น
        if not value.isdigit() or "0" in value:
            self.is_generating = True
            instance.text = instance.last_text
            self.is_generating = False
            return

        # =====================================
        # 2. ทำงานใน "โหมดจดโน้ต" (Note: ON)
        # =====================================
        if self.note_mode:
            # [แก้ไข] เช็คว่าเป็นการกดลบ (Backspace) หรือพิมพ์เพิ่ม
            if len(value) < len(instance.last_text):
                # ถ้าผู้ใช้กดลบ ให้ยอมรับค่าที่เหลืออยู่ได้เลย
                final_notes = "".join(sorted(set(value)))
            else:
                # [แก้ไข] หาตัวอักษรที่เพิ่งพิมพ์เข้ามาใหม่จริงๆ (แก้ปัญหาเคอร์เซอร์ไม่ได้อยู่ท้ายสุด)
                new_char = None
                for c in value:
                    if value.count(c) > instance.last_text.count(c):
                        new_char = c
                        break
                
                old_chars = set(instance.last_text) if instance.is_note else set()
                
                if new_char:
                    if new_char in old_chars:
                        old_chars.remove(new_char) # มีอยู่แล้วให้ลบออก (Toggle Off)
                    else:
                        old_chars.add(new_char)    # ยังไม่มีให้เพิ่มเข้าไป (Toggle On)
                
                final_notes = "".join(sorted(old_chars))

            # [แก้ไข] บันทึกการจดโน้ตลงประวัติ เพื่อให้ปุ่ม Undo/Redo ทำงานได้
            app.record_history(
                index=instance.cell_index,
                old_text=instance.last_text, new_text=final_notes,
                old_color=instance.foreground_color[:], new_color=[0.5, 0.5, 0.5, 1],
                old_readonly=instance.readonly, new_readonly=False,
                score_diff=0
            )

            self.is_generating = True
            instance.text = final_notes
            instance.last_text = final_notes
            instance.font_size = 26           
            instance.foreground_color = [0.5, 0.5, 0.5, 1] 
            instance.is_note = True
            self.engine.board[row][col] = 0    
            self.is_generating = False
            return

        # =====================================
        # 3. ทำงานใน "โหมดตอบปกติ" (Note: OFF)
        # =====================================
        if len(value) > 1 or instance.is_note:
            # [แก้ไข] ถ้าเปลี่ยนจาก Note เป็นตอบปกติ ให้หาเลขล่าสุดที่พึ่งกดจริงๆ
            new_char = None
            for c in value:
                if value.count(c) > instance.last_text.count(c):
                    new_char = c
                    break
            value = new_char if new_char else value[-1]

        num = int(value)
        is_correct = self.engine.check_move(row, col, num)
        
        old_color = instance.foreground_color[:]
        old_readonly = instance.readonly

        if is_correct:
            new_color = [0, 0.6, 0, 1] # สีเขียว
            new_readonly = True
            score_diff = 100
        else:
            new_color = [0.9, 0.1, 0.1, 1] # สีแดง
            new_readonly = False 
            score_diff = -20

        app.record_history(
            index=instance.cell_index,
            old_text=instance.last_text, new_text=value,
            old_color=old_color, new_color=new_color,
            old_readonly=old_readonly, new_readonly=new_readonly,
            score_diff=score_diff
        )

        self.is_generating = True
        instance.foreground_color = new_color
        instance.readonly = new_readonly
        instance.last_text = value
        instance.is_note = False
        instance.font_size = 26 # คืนค่าเป็นตัวใหญ่
        self.engine.board[row][col] = num 
        self.is_generating = False
        app.update_score(score_diff)

        if is_correct and self.engine.is_game_won():
            app.show_win_popup()
    def clear_board(self, instance=None):
        self.is_generating = True  
        for cell in self.cells:
            cell.text = ''
            cell.last_text = ''
            cell.readonly = False
            cell.background_color = [1, 1, 1, 1]
            cell.foreground_color = [0, 0, 0, 1]  
        self.engine.board = [[0 for _ in range(9)] for _ in range(9)]
        self.is_generating = False 

    def new_game(self, difficulty="Easy"):
        self.clear_board()
        self.is_generating = True  
        board_data = self.engine.generate_board(difficulty)
        for i in range(81):
            row = i // 9
            col = i % 9
            val = board_data[row][col]
            cell = self.cells[i]
            if val != 0:
                cell.text = str(val)
                cell.last_text = str(val)
                cell.readonly = True
                cell.background_color = [0.9, 0.9, 0.9, 1] 
                cell.foreground_color = [0, 0, 0, 1] 
            else:
                cell.text = ''
                cell.last_text = ''
                cell.readonly = False
                cell.background_color = [1, 1, 1, 1]    
                cell.foreground_color = [0, 0, 0, 1] 
        self.is_generating = False
    
    def get_hint_data(self):
        for i, cell in enumerate(self.cells):
            if cell.readonly:
                continue
            row = i // 9
            col = i % 9
            correct_val = self.engine.solution[row][col]
            if cell.text == '' or cell.text != str(correct_val):
                return i, correct_val
        return None, None


Window.size = (500, 700) 
Window.clearcolor = (0.05, 0.08, 0.15, 1)

class SudokuApp(App):
    def build(self):
        self.store = JsonStore('sudoku_save.json')
        self.undo_stack = []
        self.redo_stack = []
        self.current_difficulty = "Easy" # เก็บสถานะความยาก

        # 1. สร้าง ScreenManager เป็นตัวคุมหน้าจอทั้งหมด
        self.sm = ScreenManager()

        # ==========================================
        # 2. สร้างหน้าจอ Main Menu แบบ Modern
        # ==========================================
        menu_screen = Screen(name='menu')
        menu_layout = BoxLayout(orientation='vertical', padding=40, spacing=15)
        
        # หัวข้อแอป
        title_box = BoxLayout(orientation='vertical', size_hint=(1, 0.35))
        title = Label(text="SUDOKU", font_size=60, color=[0.3, 0.7, 1, 1], bold=True)
        subtitle = Label(text="Select Difficulty to Play", font_size=18, color=[0.6, 0.7, 0.8, 1])
        title_box.add_widget(title)
        title_box.add_widget(subtitle)
        menu_layout.add_widget(title_box)
        
        self.stats_label = Label(text=self.get_stats_text(), font_size=18, color=[1, 0.8, 0.2, 1], size_hint=(1, 0.25), halign='center', markup=True)
        menu_layout.add_widget(self.stats_label)

        # [UI Magic 2] background_normal='' ทำให้ปุ่มสีสดและไม่มีเงาดำเทาๆ มาบัง
        btn_easy = Button(text="EASY", font_size=24, bold=True, size_hint=(1, 0.15), 
                          background_normal='', background_color=[0.2, 0.8, 0.4, 1])
        btn_easy.bind(on_press=lambda inst: self.start_new_game("Easy"))
        menu_layout.add_widget(btn_easy)
        
        btn_medium = Button(text="MEDIUM", font_size=24, bold=True, size_hint=(1, 0.15), 
                            background_normal='', background_color=[0.9, 0.6, 0.1, 1])
        btn_medium.bind(on_press=lambda inst: self.start_new_game("Medium"))
        menu_layout.add_widget(btn_medium)
        
        btn_hard = Button(text="HARD", font_size=24, bold=True, size_hint=(1, 0.15), 
                          background_normal='', background_color=[0.9, 0.3, 0.3, 1])
        btn_hard.bind(on_press=lambda inst: self.start_new_game("Hard"))
        menu_layout.add_widget(btn_hard)

        btn_quit = Button(text="QUIT", font_size=24, bold=True, size_hint=(1, 0.15), 
                          background_normal='', background_color=[0.4, 0.4, 0.5, 1])
        btn_quit.bind(on_press=lambda inst: self.stop())
        menu_layout.add_widget(btn_quit)

        menu_screen.add_widget(menu_layout)
        self.sm.add_widget(menu_screen)
        # ==========================================
        # 3. สร้างหน้าจอ Game Screen ให้เข้าธีม
        # ==========================================
        game_screen = Screen(name='game')
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.seconds_elapsed = 0
        self.timer_event = None
        self.score = 0
        
        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)
        btn_back_menu = Button(text="< Menu", font_size=18, bold=True, size_hint=(0.25, 1), 
                               background_normal='', background_color=[0.4, 0.4, 0.5, 1])
        btn_back_menu.bind(on_press=self.go_to_menu)
        
        self.timer_label = Label(text="Time: 00:00", font_size=20, bold=True, size_hint=(0.35, 1), color=[1, 1, 1, 1])
        self.score_label = Label(text="Score: 0", font_size=20, bold=True, color=[1, 0.8, 0.2, 1], size_hint=(0.4, 1)) 
        
        top_bar.add_widget(btn_back_menu)
        top_bar.add_widget(self.timer_label)
        top_bar.add_widget(self.score_label)
        main_layout.add_widget(top_bar)

        self.board = SudokuBoard(size_hint=(1, 0.65)) 
        main_layout.add_widget(self.board)
        
# [ปรับปรุง] ลดไซส์ฟอนต์ปุ่มนิดนึง และเพิ่มปุ่ม Note ลงไปในแถว
        row1_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.10), spacing=5)
        btn_new = Button(text="Restart", font_size=15, bold=True, background_normal='', background_color=[0.2, 0.6, 0.9, 1]) 
        btn_clear = Button(text="Clear", font_size=15, bold=True, background_normal='', background_color=[0.9, 0.3, 0.3, 1])
        btn_hint = Button(text="Hint", font_size=15, bold=True, background_normal='', background_color=[0.9, 0.6, 0.1, 1])
        
        self.btn_note = ToggleButton(text="Note: OFF", font_size=14, bold=True, background_normal='',background_down='', background_color=[0.5, 0.5, 0.6, 1])
        self.btn_note.bind(state=self.toggle_note) # ผูกคำสั่งเปิด-ปิด
        
        btn_new.bind(on_press=lambda inst: self.start_new_game(self.current_difficulty))
        btn_clear.bind(on_press=self.clear_game)
        btn_hint.bind(on_press=self.give_hint)
        
        row1_layout.add_widget(btn_new)
        row1_layout.add_widget(btn_clear)
        row1_layout.add_widget(btn_hint)
        row1_layout.add_widget(self.btn_note) # ใส่ปุ่มลงแถว
        main_layout.add_widget(row1_layout)

        row2_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.10), spacing=10)
        btn_undo = Button(text="Undo", font_size=18, bold=True, background_normal='', background_color=[0.6, 0.6, 0.7, 1])
        btn_redo = Button(text="Redo", font_size=18, bold=True, background_normal='', background_color=[0.6, 0.6, 0.7, 1])
        btn_undo.bind(on_press=self.undo_move)
        btn_redo.bind(on_press=self.redo_move)
        row2_layout.add_widget(btn_undo)
        row2_layout.add_widget(btn_redo)
        main_layout.add_widget(row2_layout)

        row3_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.10), spacing=10)
        btn_save = Button(text="Save Game", font_size=18, bold=True, background_normal='', background_color=[0.3, 0.8, 0.5, 1])
        btn_load = Button(text="Load Game", font_size=18, bold=True, background_normal='', background_color=[0.8, 0.4, 0.7, 1])
        btn_save.bind(on_press=self.save_game)
        btn_load.bind(on_press=self.load_game)
        row3_layout.add_widget(btn_save)
        row3_layout.add_widget(btn_load)
        main_layout.add_widget(row3_layout)

        game_screen.add_widget(main_layout)
        self.sm.add_widget(game_screen)

        return self.sm

    def update_timer(self, dt):
        self.seconds_elapsed += 1
        minutes = self.seconds_elapsed // 60
        seconds = self.seconds_elapsed % 60
        self.timer_label.text = f"Time: {minutes:02d}:{seconds:02d}"

    def update_score(self, points):
        self.score += points
        self.score_label.text = f"Score: {self.score}"

    # เปลี่ยนมารับค่า difficulty แทน instance
    def start_new_game(self, difficulty):
        self.current_difficulty = difficulty
        self.board.new_game(difficulty) # ส่งความยากไปให้กระดานสร้างโจทย์
        self.seconds_elapsed = 0
        self.timer_label.text = "Time: 00:00"
        self.score = 0
        self.score_label.text = "Score: 0"
        self.undo_stack.clear() 
        self.redo_stack.clear()
        
        if self.timer_event:
            self.timer_event.cancel()
        self.timer_event = Clock.schedule_interval(self.update_timer, 1)

        # สลับหน้าต่างไปที่หน้าเล่นเกม ('game')
        self.sm.transition.direction = 'left'

        self.sm.current = 'game'
    def clear_game(self, instance):
        self.board.clear_board() 
        if self.timer_event:
            self.timer_event.cancel()
        self.score = 0
        self.score_label.text = "Score: 0"
        self.seconds_elapsed = 0
        self.timer_label.text = "Time: 00:00"
        self.undo_stack.clear()
        self.redo_stack.clear()

    # --- ฟังก์ชันจัดการประวัติ Undo / Redo ---
    def record_history(self, index, old_text, new_text, old_color, new_color, old_readonly, new_readonly, score_diff):
        action = {
            'index': index, 'old_text': old_text, 'new_text': new_text,
            'old_color': old_color, 'new_color': new_color,
            'old_readonly': old_readonly, 'new_readonly': new_readonly,
            'score_diff': score_diff
        }
        self.undo_stack.append(action)
        self.redo_stack.clear() # ถ้าเดินใหม่ ให้ทิ้งอนาคตที่ Redo ได้ทิ้งไป

    def undo_move(self, instance):
        if not self.undo_stack:
            print("🚫 สุดทางแล้ว ไม่มีอะไรให้ Undo!")
            return
            
        action = self.undo_stack.pop()
        self.redo_stack.append(action) # เก็บใส่อนาคตเผื่อเปลี่ยนใจ Redo
        
        cell = self.board.cells[action['index']]
        self.board.is_generating = True
        cell.text = action['old_text']
        cell.last_text = action['old_text']
        cell.foreground_color = action['old_color']
        cell.readonly = action['old_readonly']
        val = action['old_text']
        self.board.engine.board[action['index'] // 9][action['index'] % 9] = int(val) if val else 0
        self.board.is_generating = False
        
        self.update_score(-action['score_diff']) # คืนคะแนนกลับ

    def redo_move(self, instance):
        if not self.redo_stack:
            print("🚫 ไม่มีอะไรให้ Redo แล้ว!")
            return
            
        action = self.redo_stack.pop()
        self.undo_stack.append(action) # คืนกลับไปในประวัติ
        
        cell = self.board.cells[action['index']]
        self.board.is_generating = True
        cell.text = action['new_text']
        cell.last_text = action['new_text']
        cell.foreground_color = action['new_color']
        cell.readonly = action['new_readonly']
        val = action['new_text']
        self.board.engine.board[action['index'] // 9][action['index'] % 9] = int(val) if val else 0
        self.board.is_generating = False
        
        self.update_score(action['score_diff']) # คิดคะแนนใหม่

    def save_game(self, instance):
        cells_data = []
        for cell in self.board.cells:
            cells_data.append({
                'text': cell.text, 'readonly': cell.readonly,
                'bg_color': cell.background_color, 'fg_color': cell.foreground_color,
                'last_text': cell.last_text
            })
        self.store.put('saved_level', 
                       time=self.seconds_elapsed, score=self.score,
                       board_engine=self.board.engine.board,
                       solution_engine=self.board.engine.solution,
                       cells=cells_data)
        print("🟢 บันทึกเกมสำเร็จ!")

    def load_game(self, instance):
        if self.store.exists('saved_level'):
            data = self.store.get('saved_level')
            self.seconds_elapsed = data['time']
            minutes = self.seconds_elapsed // 60
            seconds = self.seconds_elapsed % 60
            self.timer_label.text = f"Time: {minutes:02d}:{seconds:02d}"
            
            self.score = data['score']
            self.score_label.text = f"Score: {self.score}"
            
            self.board.engine.board = data['board_engine']
            self.board.engine.solution = data['solution_engine']
            
            self.board.is_generating = True
            for i, cell_data in enumerate(data['cells']):
                cell = self.board.cells[i]
                cell.text = cell_data['text']
                cell.last_text = cell_data.get('last_text', '') # ดึงค่าเก่ากลับมาด้วย
                cell.readonly = cell_data['readonly']
                cell.background_color = cell_data['bg_color']
                cell.foreground_color = cell_data['fg_color']
            self.board.is_generating = False
            
            self.undo_stack.clear() # โหลดเซฟมาใหม่ ล้างประวัติการเดิน
            self.redo_stack.clear()

            if self.timer_event:
                self.timer_event.cancel()
            self.timer_event = Clock.schedule_interval(self.update_timer, 1)
            print("🟠 โหลดเกมสำเร็จ!")
        else:
            print("🔴 ไม่พบไฟล์เซฟเก่า!")

    def give_hint(self, instance):
        cell_index, correct_val = self.board.get_hint_data()
        
        if cell_index is not None:
            cell = self.board.cells[cell_index]
            old_color = cell.foreground_color[:]
            old_readonly = cell.readonly
            
            # บันทึกประวัติเพื่อให้ Hint ก็ Undo ได้
            self.record_history(
                index=cell_index,
                old_text=cell.last_text, new_text=str(correct_val),
                old_color=old_color, new_color=[0, 0.4, 1, 1],
                old_readonly=old_readonly, new_readonly=True,
                score_diff=-30
            )

            self.board.is_generating = True
            cell.text = str(correct_val)
            cell.last_text = str(correct_val)
            cell.foreground_color = [0, 0.4, 1, 1] 
            cell.readonly = True
            self.board.is_generating = False
            cell.readonly = True
            row = cell_index // 9
            col = cell_index % 9
            self.board.engine.board[row][col] = correct_val
            self.update_score(-30)
            if self.board.engine.is_game_won():
                self.show_win_popup()

        else:
            print("✨ กระดานสมบูรณ์แล้ว ไม่มีอะไรให้ใบ้!")

    def show_win_popup(self):
        if self.timer_event:
            self.timer_event.cancel()
        #ทำสถิติใหม่หรือเปล่า เช็คจากคะแนนและเวลา แล้วบันทึกถ้าเป็นสถิติใหม่
        key = f"stats_{self.current_difficulty}"
        is_new_record = False
        
        # เช็คว่าเคยมีสถิติเก่าไหม
        if self.store.exists(key):
            best = self.store.get(key)
            # ถ้าคะแนนเยอะกว่า หรือ คะแนนเท่ากันแต่เวลาเร็วกว่า = สถิติใหม่!
            if self.score > best['score'] or (self.score == best['score'] and self.seconds_elapsed < best['time']):
                is_new_record = True
        else:
            is_new_record = True # ถ้ายังไม่เคยชนะโหมดนี้เลย ก็เป็นสถิติใหม่แน่นอน

        # ถ้าเป็นสถิติใหม่ ให้บันทึกลงไฟล์ และเตรียมข้อความอวยพร
        if is_new_record:
            self.store.put(key, score=self.score, time=self.seconds_elapsed)
            record_text = "\n\n NEW HIGH SCORE! "
        else:
            record_text = ""

        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        msg_label = Label(text=f"WINNER!\n\nScore: {self.score}\nTime: {self.timer_label.text.split(' ')[1]}{record_text}", 
                          halign='center', font_size=24, bold=True, color=[1, 0.8, 0.2, 1])
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.4))
        btn_close = Button(text="Close", bold=True, background_normal='', background_color=[0.4, 0.4, 0.5, 1])
        btn_menu = Button(text="Main Menu", bold=True, background_normal='', background_color=[0.2, 0.8, 0.4, 1])

        btn_layout.add_widget(btn_menu)
        btn_layout.add_widget(btn_close)
        
        content.add_widget(msg_label)
        content.add_widget(btn_layout)

        popup = Popup(title='Congratulations!', title_size=20, title_align='center', 
                      content=content, size_hint=(0.85, 0.45), auto_dismiss=False, separator_color=[0.2, 0.8, 0.4, 1])
        
        def back_to_menu_from_popup(inst):
            popup.dismiss()
            self.go_to_menu(None)
            
        btn_close.bind(on_press=popup.dismiss)
        btn_menu.bind(on_press=back_to_menu_from_popup)
        
        popup.open()
    # [เพิ่ม] ฟังก์ชันจัดการเปิดปิดโหมดจดโน้ต
    def toggle_note(self, instance, value):
        if value == 'down':
            instance.text = "Note: ON"
            instance.background_color = [0.2, 0.8, 0.4, 1] # สีเขียว
            self.board.note_mode = True
        else:
            instance.text = "Note: OFF"
            instance.background_color = [0.5, 0.5, 0.6, 1] # สีเทา
            self.board.note_mode = False

    def get_stats_text(self):
        # [ตกแต่ง] ใช้ Kivy Markup เปลี่ยนสีตัวหนังสือแบบไล่เฉดสี
        text = "[b][size=22][color=ffcc00] BEST RECORDS [/color][/size][/b]\n\n"
        
        # กำหนดสีให้เข้ากับปุ่ม (Easy=เขียว, Medium=ส้ม, Hard=แดง)
        diff_colors = {"Easy": "33cc66", "Medium": "f29c1f", "Hard": "e64d4d"}
        
        for diff in ["Easy", "Medium", "Hard"]:
            key = f"stats_{diff}"
            color_hex = diff_colors[diff]
            
            if self.store.exists(key):
                data = self.store.get(key)
                mins, secs = data['time'] // 60, data['time'] % 60
                # เน้นสีระดับความยาก สีคะแนนเป็นขาว และสีเวลาเป็นเทา
                text += f"[b][color={color_hex}]{diff}:[/color][/b]  [color=ffffff]{data['score']} pts[/color]  [color=aaaaaa](Time: {mins:02d}:{secs:02d})[/color]\n"
            else:
                # ถ้ายังไม่มีสถิติ ให้ขึ้นตัวเทาๆ มืดๆ
                text += f"[b][color={color_hex}]{diff}:[/color][/b]  [color=666666]No Record[/color]\n"
                
        return text
    
    def go_to_menu(self, instance=None):
        if self.timer_event:
            self.timer_event.cancel() # หยุดเวลาเมื่อออกไปหน้าเมนู
        self.stats_label.text = self.get_stats_text()
        self.sm.transition.direction = 'right' # สั่งให้อนิเมชั่นเลื่อนไปทางขวา
        self.sm.current = 'menu' # สลับไปที่หน้า 'menu'

if __name__ == '__main__':
    SudokuApp().run()