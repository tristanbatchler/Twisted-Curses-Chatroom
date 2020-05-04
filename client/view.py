import curses
import curses.textpad

class GameView:
    def __init__(self, controller):
        self.controller = controller
        self.stdscr = None
        self.mainwin = None
        self.chatwin = None
        self.chatbox = None
    
    def start(self, stdscr: curses.window):
        self.stdscr = stdscr
        self.mainwin = stdscr.subwin(20, 100, 0, 0)
        self.chatwin = stdscr.subwin(1, 80, 20, 1)
        curses.halfdelay(1)
        curses.curs_set(False)
        
        while True:
            try:
                self.stdscr.erase()
                self.draw()
                self.stdscr.refresh()
                self.controller.chat()
            except KeyboardInterrupt:
                break

    def draw(self):
        self.mainwin.border()
        self.mainwin.addstr(0, 43, "MOONLAPSE CHAT")
        
        logsize: int = len(self.controller.log)
        for i in range(0, 19):
            if i >= logsize:
                break
            self.mainwin.addstr(i + 1, 1, self.controller.log[i])
