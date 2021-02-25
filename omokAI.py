import pygame, sys, random
from pygame.locals import *
import numpy as np
from copy import deepcopy
from enum import Enum

board_color1 = (153, 102, 000)
board_color2 = (153, 102, 51)
board_color3 = (204, 153, 000)
board_color4 = (204, 153, 51)
bg_color = (255,255,255)
black = (0,0,0)
white = (255,255,255)
red = (0,255,0)
blue = (0,0,255)
window_width = 800
window_height = 500
board_width = 500
board_size = 15
grid_size = 30
black_stone = 1
white_stone = 2
tie = 100
empty = 0



#가중치 상수 정의
G22 = 5
B22 = 15
AB33 = 100
G33 = 600
B33 = 700
G44 = 150000
A33 = 5000
A44 = 200000

class BoardState(Enum):
    EMPTY = 0
    BLACK = 1
    WHITE = 2

turn = 1                        #흑돌을 1, 백돌을 2라고 할 거임
counter = BoardState.WHITE      #상대가 흑돌일지 백돌일지 모르니까 일단 백돌로 초기화
computer = BoardState.BLACK     #자신이 흑돌일지 백돌일지 모르니까 일단 흑돌로 초기화
evaluate_array = []


class Rule(object):
    def __init__(self, board):
        self.board = board

    def is_invalid(self, x, y):
        return (x < 0 or x >= board_size or y < 0 or y >= board_size)

    #돌을 놓아보고 들어내는 함수
    def set_stone(self, x, y, stone):
        self.board[y][x] = stone

    #주어진 방향으로 같은 돌을 찾다가 다른 돌이나오면 탐색을 멈춤
    def get_xy(self, direction):
        list_dx = [-1, 1, -1, 1, 0, 0, 1, -1]
        list_dy = [0, 0, -1, 1, -1, 1, -1, 1]
        
        return list_dx[direction], list_dy[direction]
        #마지막으로 둔 위치에서 좌(-1,0) 우(1,0) 좌상(-1,-1) 우하(1,1)
        #상(0,-1) 하(0,1) 우상(1,-1) 좌하(-1,1) 를 확인

    def get_stone_count(self, x, y, stone, direction):
        x1, y1 = x, y
        cnt = 1
        for i in range(2):
            dx, dy = self.get_xy(direction * 2 + i)
            x, y = x1, y1
            while True:
                x, y = x + dx, y + dy
                if self.is_invalid(x, y) or self.board[y][x] != stone:
                    break
                else:
                    cnt += 1
        return cnt
    
    def is_gameover(self, x, y, stone):
        for i in range(4):
            cnt = self.get_stone_count(x, y, stone, i)
            if cnt >= 5:
                return cnt
        return cnt

    #5개인지 확인, 네 방향을 모두 탐색
    def is_five(self, x, y, stone):
        for i in range(4):
            cnt = self.get_stone_count(x, y, stone, i)
            if cnt == 5:
                return True
        return False

    def find_empty_point(self, x, y, stone, direction):
        dx, dy = self.get_xy(direction)
        while True:
            x, y = x + dx, y + dy
            if self.is_invalid(x, y) or self.board[y][x] != stone:
                break
        if not self.is_invalid(x, y) and self.board[y][x] == empty:
            return x, y
        else:
            return None

    #열린 3 검사
    def open_three(self, x, y, stone, direction):
        for i in range(2):
            coord = self.find_empty_point(x, y, stone, direction * 2 + i)
            if coord:
                dx, dy = coord
                self.set_stone(dx, dy, stone)
                if 1 == self.open_four(dx, dy, stone, direction):
                    if not self.forbidden_point(dx, dy, stone):
                        self.set_stone(dx, dy, empty)
                        return True
                self.set_stone(dx, dy, empty)
        return False

    #열린 3에서 한쪽에 돌을 하나 더 두었을 때 생기는 열린 4
    def open_four(self, x, y, stone, direction):
        cnt = 0
        for i in range(2):
            coord = self.find_empty_point(x, y, stone, direction * 2 + i)
            if coord:
                if self.five(coord[0], coord[1], stone, direction):
                    cnt += 1
        if cnt == 2:
            if 4 == self.get_stone_count(x, y, stone, direction):
                cnt = 1
        else: cnt = 0
        return cnt

    #4는 게임이 끝날 수도있어서 검사
    def four(self, x, y, stone, direction):
        for i in range(2):
            coord = self.find_empty_point(x, y, stone, direction * 2 + i)
            if coord:
                if self.five(coord[0], coord[1], stone, direction):
                    return True
        return False

    # 5 검사 : 열린4나 그냥 4를 검사할때 그 방향에서 오목이 되는지 검사할 때 사용
    def five(self, x, y, stone, direction):
        if 5 == self.get_stone_count(x, y, stone, direction):
            return True
        return False

    #33검사
    def double_three(self, x, y, stone):
        cnt = 0
        self.set_stone(x, y, stone)
        for i in range(4):
            if self.open_three(x, y, stone, i):
                cnt += 1
        self.set_stone(x, y, empty)
        #열린3의 개수가 3이상이면 33으로 true 반환
        if cnt >= 2:
            print("double three")
            return True
        return False

    #44검사
    def double_four(self, x, y, stone):
        cnt = 0
        self.set_stone(x, y, stone)
        for i in range(4):
            if self.open_four(x, y, stone, i) == 2:
                cnt += 2
            elif self.four(x, y, stone, i):
                cnt += 1
        self.set_stone(x, y, empty)
        if cnt >= 2:
            print("double four")
            return True
        return False

    def forbidden_point(self, x, y, stone):
        #두었을 때 오목이 되면, 금수는 해제됨 왜냐면 바로 게임 끝
        if self.is_five(x, y, stone):
            return False
        elif 5 < self.is_gameover(x, y, stone):
            print("overline")
            return True
        elif self.double_three(x, y, stone) or self.double_four(x, y, stone):
            return True
        return False

    #금수 자리를 찾아서 좌표를 반환하는 함수
    def get_forbidden_points(self, stone):
        coords = []
        for y in range(len(self.board)):
            for x in range(len(self.board[0])):
                if self.board[y][x]:
                    continue
                if self.forbidden_point(x, y, stone):
                    coords.append((x, y))
        return coords


def main():
    global white_img, black_img
    pygame.init()
    surface = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("Omok game")

    surface.fill(bg_color)
    omok = Omok(surface)
    menu = Menu(surface)
    
    
   
    while True:
        ai = AI(omok,BoardState.BLACK,2)
        ai2 = AI(omok,BoardState.WHITE, 1)
        result = BoardState.EMPTY
        enable_ai = True
        enable_ai2 = False
        ai.first()
        result = omok.get_board_result()
        omok.change_state()
        omok.init_game()
        while True :    
            if enable_ai2 :
                ai2.one_step()
                result = omok.get_board_result()
                if result != BoardState.EMPTY :
                    break
                if enable_ai :
                    ai.one_step()
                    result = omok.get_board_result()

                    if result != BoardState.EMPTY :
                        break
                else :
                    omok.change_state()

            for event in pygame.event.get() :
                if event.type == QUIT : exit()
                elif event.type == MOUSEBUTTONDOWN : 
                    (x,y) = pygame.mouse.get_pos()
                    omok.set_board(x,y,BoardState.BLACK)
                    if omok.get_board()[y][x] == BoardState.EMPTY :
                        result = omok.get_board_result()
                    else : continue
                    if result != BoardState.EMPTY : break
                    if enable_ai :
                        ai.one_step()
                        result = omok.get_board_result()
                    else : omok.change_state()
            if omok.is_gameover:
                return

            pygame.display.update()
        menu.is_continue(omok)
        omok.__board.zeros() #점수판 초기화


class AI(object) :
    def __init__(self, Omok, currentState, depth) :
        self.__omok = Omok
        self.__currentState = currentState
        self.__depth = depth
        self.__currentI = -1
        self.__currentJ = -1
    
    def set_board(self,i,j,state,) : 
        self.__omok.set_board(i,j,state)

    # 44 ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def G_44(self, board_list, weightboard_list):
        board = np.reshape(board_list, (15,15))
        weightboard = np.reshape(weightboard_list, (15,15))
        two = counter
        zero = 0

        for i in range(2,11) :
            for j in range(0,14) : 
                #122220가로
                if board[j][i-2] == computer and board[j][i-1] == counter and board[j][i] == counter and board[j][i+1] == counter and board[j][i+2] == counter and board[j][i+3] == 0:
                    weightboard[j][i+3] += G44
                #022221가로
                if board[j][i-2] == 0 and board[j][i-1] == counter and board[j][i] == counter and board[j][i+1] == counter and board[j][i+2] == counter and board[j][i+3] == computer:
                    weightboard[j][i+3] += G44
                #122220세로
                if board[i-2][j] == computer and board[i-1][j] == counter and board[j][i] == counter and board[i+1][j] == counter and board[i+2][j] == counter and board[i+3][j] == 0:
                    weightboard[i+3][j] += G44
                #022221세로
                if board[i-2][j] == 0 and board[i-1][j] == counter and board[j][i] == counter and board[i+1][j] == counter and board[i+2][j] == counter and board[i+3][j] == 0:
                    weightboard[i-2][j] += G44

        for k in range(2) :
            for i in range(2,12) :
                for j in range(0,14) :
                    #22202 or 20222 가로
                    if board[j][i-2] == counter and board[j][i-1] == two and board[j][i] == counter and board[j][i+1] == zero and board[j][i+2] == counter :
                        if k == 0 : weightboard[j][i+1] += G44
                        elif k == 1 : weightboard[j][i-1] += G44
                    #세로
                    if board[i-2][j] == counter and board[i-1][j] == two and board[i][j] == counter and board[i+1][j] == zero and board[i+2][j] == counter :
                        if k == 0 : weightboard[i+1][j] += G44
                        elif k == 1 : weightboard[i-1][j] += G44
            temp = two
            two = zero
            zero = temp

        for i in range(2,12) :
            for j in range(0,14) :
                #22022가로
                if board[j][i-2] == counter and board[j][i-1] == counter and board[j][i] == 0 and board[j][i+1] == counter and board[j][i+2] == counter :
                    weightboard[j][i] += G44
                #세로
                if board[i-2][j] == counter and board[i-1][j] == counter and board[i][j] == 0 and board[i+1][j] == counter and board[i+2][j] == counter :
                    weightboard[i][j] += G44

        for i in range(3,11) : 
            for j in range(2,11) :
                #대각 122220
                if board[j-2][i-2] == computer and board[j-1][i-1] == counter and board[j][i] == counter and board[j+1][i+1] == counter and board[j+2][i+2] == counter and board[j+3][i+3] == 0 :
                    weightboard[j+3][i+3] += G44
                #대각 022221
                if board[j-2][i-2] == 0 and board[j-1][i-1] == counter and board[j][i] == counter and board[j+1][i+1] == counter and board[j+2][i+2] == counter and board[j+3][i+3] == computer :
                    weightboard[j-2][i-2] += G44
                #반대각 122220
                if board[j-2][i+2] == computer and board[j-1][i+1] == counter and board[j][i] == counter and board[j+1][i-1] == counter and board[j+2][i-2] == counter and board[j+3][i-3] == 0 :
                    weightboard[j+3][i-3] += G44
                #반대각 022221
                if board[j-2][i+2] == 0 and board[j-1][i+1] == counter and board[j][i] == counter and board[j+1][i-1] == counter and board[j+2][i-2] == counter and board[j+3][i-3] == computer :
                    weightboard[j+-2][i+2] += G44

        for k in range(2) :
            for i in range(2,12) :
                for j in range(2,12) :
                    #대각 22202 20222
                    if board[j-2][i-2] == counter and board[j-1][i-1] == two and board[j][i] == counter and board[j+1][i+1] == zero and board[j+2][i+2] == counter :
                        if k == 0 : weightboard[j+1][i+1] += G44
                        elif k == 1 : weightboard[j-1][i-1] += G44
                    #반대각 22202 20222
                    if board[j-2][i+2] == counter and board[j-1][i+1] == two and board[j][i] == counter and board[j+1][i-1] == zero and board[j+2][i-2] == counter :
                        if k == 0 : weightboard[j+1][i-1] += G44
                        elif k == 1 : weightboard[j-1][i+1]+= G44
            temp = two
            two = zero
            zero = temp

        for i in range(2,12) :
            for j in range(2,12) :
                #대각 22022
                if board[j-2][i-2] == counter and board[j-1][i-1] == counter and board[j][i] == 0 and board[j+1][i+1] == counter and board[j+2][i+2] == counter :
                    weightboard[j][i] += G44
                if board[j-2][i+2] == counter and board[j-1][i+1] == counter and board[j][i] == 0 and board[j+1][i-1] == counter and board[j+2][i-2] == counter :
                    weightboard[j][i]+= G44

        return board, weightboard


    # 33 ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def G_33(self, board_list, weightboard_list) :
        board = np.reshape(board_list, (15,15))
        weightboard = np.reshape(weightboard_list, (15,15))
        find33 = 0
        two = counter 
        zero = 0
        
        for i in range(2,12) :
            for j in range(0,14) :
                #02220가로
                if board[j][i-2] == 0 and board[j][i-1] == counter and board[j][i] == counter and board[j][i+1] == counter and board[j][i+2] == 0 :
                    weightboard[j][i-2] += G33
                    weightboard[j][i+2] += G33
                    find33 = find33 + 1
                #02220세로
                if board[i-2][j] == 0 and board[i-1][j] == counter and board[i][j] == counter and board[i+1][j] ==counter and board[i+2][j] == 0 :
                    weightboard[i-2][j] += G33
                    weightboard[i+2][j] += G33
                    find33 = find33 + 1

        for k in range(2) :
            for i in range(2,11) :
                for j in range(0,14) :
                    #020220 or 022020 가로
                    if board[j][i-2] == 0 and board[j][i-1] == counter and board[j][i] ==two and board[j][i+1] == zero and board[j][i+2] == counter and board[j][i+3] == 0 :
                        if k == 0 : weightboard[j][i+1] += G33
                        elif k == 1 : weightboard[j][i] += G33
                        find33 = find33 + 1
                    #022020 or 020220 세로
                    if board[i-2][j] == 0 and board[i-1][j] == counter and board[i][j] == two and board[i+1][j] == zero and board[i+2][j] == counter and board[i+3][j] == 0 :
                        if k==0 : weightboard[i+1][j] += G33
                        elif k==1 : weightboard[i][j] += G33 
                        find33 = find33 + 1
        temp = two
        two = zero
        zero = temp

        for i in range(2,12) :
            for j in range(2,12) :
                #02220 대각
                if board[j-2][i-2] == 0 and board[j-1][i-1] == counter and board[j][i] == counter and board[j+1][i+1] == counter and board[j+2][i+2] == 0 :
                    weightboard[j-2][i-2] += G33
                    weightboard[j+2][i+2] += G33
                #02220 반대각
                if board[j-2][i+2] == 0 and board[j-1][i+1] == counter and board[j][i] == counter and board[j+1][i-1] == counter and board[j+2][i-2] == 0 :
                    weightboard[j-2][i+2] += G33
                    weightboard[j+2][i-2] += G33

        for k in range(2) :
            for i in range(2,11) :
                for j in range(3,11) :
                    #020220 or 022020 대각
                    if board[j-2][i-2] == 0 and board[j-1][i-1] == counter and board[j][i] ==two and board[j+1][i+1] == zero and board[j+2][i+2] == counter and board[j+3][i+3] == 0 :
                        if k == 0 : weightboard[j+1][i+1] += G33
                        elif k == 1 : weightboard[j][i] += G33
                        find33 = find33 + 1
                    #022020 or 020220 반대각
                    if board[i-2][j+2] == 0 and board[i-1][j+1] == counter and board[i][j] == two and board[i+1][j-1] == zero and board[i+2][j-2] == counter and board[i+3][j-3] == 0 :
                        if k==0 : weightboard[i+1][j] += G33
                        elif k==1 : weightboard[i][j] += G33
                        find33 = find33 + 1
            temp = two
            two = zero
            zero = temp
        return find33


    # Attack3 ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def A_33(self,board_list, weightboard_list) :
        board = np.reshape(board_list, (15,15))
        weightboard = np.reshape(weightboard_list, (15,15))
        zero = 0
        two = computer
        find33 = 0
        g33 = A33 + 5000   

        for i in range(2,12) :
            for j in range(0,14) :
                #01110 가로
                if board[j][i-2] == 0 and board[j][i-1] == computer and board[j][i] == computer and board[j][i+1] == computer and board[j][i+2] == 0 :
                    weightboard[j][i-2] += g33
                    weightboard[j][i+2] += g33
                    find33 = find33 + 1
                #01110 세로
                if board[i-2][j] == 0 and board[i-1][j] == computer and board[i][j] == computer and board[i+1][j] == computer and board[i+2][j] ==0 :
                    weightboard[i-2][j] += g33
                    weightboard[i+2][j] += g33
                    find33 = find33 + 1
        
        for k in range(2) :
            for i in range(2,11) :
                for j in range (0,14) :
                    #011010 or 010110 가로
                    if board[j][i-2] == 0 and board[j][i-1] == computer and board[j][i] == two and board[j][i+1] == zero and board[j][i+2] == computer and board[j][i+3] == 0:
                        if k == 0 : weightboard[j][i+1] += g33
                        elif k == 1 : weightboard[j][i] += g33
                        find33 = find33 + 1
                    #011010 or 010110 세로
                    if board[i-2][j] == 0 and board[i-1][j] == computer and board[i][j] == two and board[i+1][j] == zero and board[i+2][j] == computer and board[i+3][j] == 0 :
                        if k == 0 : weightboard[i][j] += g33
                        elif k == 1 : weightboard[i+1][j] += g33
                        find33 = find33 + 1
            temp = two
            two = zero
            zero = temp
        
        for i in range(2,12) :
            for j in range(2,12) :
                #01110 대각
                if board[j-2][i-2] == 0 and board[j-1][i-1] == computer and board[j][i] == computer and board[j+1][i+1] == computer and board[j+2][i+2] == 0 :
                    weightboard[j-2][i-2] += g33
                    weightboard[j+2][i+2] += g33
                    find33 = find33 + 1
                #반대각
                if board[j+2][i-2] == 0 and board[j+1][i-1] == computer and board[j][i] == computer and board[j-1][i+1] == computer and board[j-2][i+2] == 0 :
                    weightboard[j+2][i-2] += g33
                    weightboard[j-2][i+2] += g33
                    find33 = find33 + 1
                
        for k in range(2) :
            for i in range(2,11) :
                for j in range(3,11) :
                    #011010 010110대각
                    if board[j-2][i-2] == 0 and board[j-1][i-1] == computer and board[j][i] == two and board[j+1][i+1] == zero and board[j+2][i+2] == computer and board[j+3][i+3] == 0 :
                        if k == 0 : weightboard[j+1][i+1] += g33
                        elif k == 1 : weightboard[j][i] += g33
                        find33 = find33 + 1
                    #반대각
                    if board[j+2][i-2] == 0 and board[j+1][i-1] == computer and board[j][i] == two and board[j-1][i+1] ==zero and board[j-2][i+2] == computer and board[j-3][i+3] == 0 :
                        if k == 0 : weightboard[j-1][i+1] += g33
                        elif k == 1 : weightboard[j][i] += g33
                        find33 = find33 + 1

        return board, weightboard


    # Blocked G3 ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def B_G33(self,find33, board_list, weightboard_list) : 
        board = np.reshape(board_list, (15,15))
        weightboard = np.reshape(weightboard_list, (15,15))
        zero = 0
        zero2 = 0
        one = computer
        two = counter

        #12220 가로세로
        for k in range(0,2) :
            for i in range(2,12) :
                for j in range(0,14) :
                    if board[j][i-2] == one and board[j][i-1] == counter and board[j][i] == counter and board[j][i+1] == counter and board[j][i+2] == zero :
                        if k ==0 :
                            weightboard[j][i+2] += G33
                            if find33 >= 1 : weightboard[j][i+2] -= B33
                        elif k == 1 :
                            weightboard[j][i-2] += G33
                            if find33 >= 1 : weightboard[j][i-2] -= B33
                    if board[i-2][j] == one and board[i-1][j] == counter and board[i][j] == counter and board[i+1][j] == counter and board[i+2][j] == zero :
                        if k == 0 :
                            weightboard[i+2][j] += G33
                            if find33 >= 1 : weightboard[i+2][j] -= B33
                        elif k == 1 :
                            weightboard[i-2][j] += G33
                            if find33 >= 1 : weightboard[i-2][j] -= B33                       
            temp = one
            one = zero
            zero = temp

        #120220 122020 가로세로
        for l in range(2) :
            for k in range(2) : 
                for i in range(2,11) :
                    for j in range(0,14) :
                        if board[j][i-2] == one and board[j][i-1] == counter and board[j][i] == two and board[j][i+1] == zero and board[j][i+2] == counter and board[j][i+3] == zero2 :
                            if l ==0 :
                                weightboard[j][i+3] += G33
                                if find33 >= 1 : weightboard[j][i+3] -= B33 
                            elif l == 1 :
                                weightboard[j][i-2] += G33
                                if find33 >= 1 : weightboard[j][i-2] -= B33 
                        if board[i-2][j] == one and board[i-1][j] == counter and board[i][j] == two and board[i+1][j] == zero and board[i+2][j] == counter and board[i+3][j] == zero2 :
                            if l ==0 :
                                weightboard[i+3][j] += G33
                                if find33 >= 1 : weightboard[i+3][j] -= B33 
                            elif l == 1 :
                                weightboard[i-2][j] += G33
                                if find33 >= 1 : weightboard[i-2][j] -= B33 
                temp = two
                two = zero
                zero = temp
            temp = one
            one = zero2
            zero2 = temp
        
        #12220 대각 반대각
        for k in range(2) :
            for i in range(2,12) :
                for j in range(2, 12) :
                    if board[j-2][i-2] == one and board[j-1][i-1] == counter and board[j][i] == counter and board[j+1][i+1] == counter and board[j+2][i+2] == zero :
                        if k == 0 : 
                            weightboard[j+2][i+2] += G33
                            if find33 >= 1 : weightboard[j+2][i+2] -= B33 
                        elif k == 1 :
                            weightboard[j-2][i-2] += G33
                            if find33 >= 1 : weightboard[j-2][i-2] -= B33 
                    if board[j+2][i-2] == one and board[j+1][i-1] == counter and board[j][i] == counter and board[j-1][i+1] == counter and board[j-2][i+2] == zero :
                        if k == 0:
                            weightboard[j-2][i+2] += G33
                            if find33 >= 1 : weightboard[j-2][i+2] -= B33 
                        elif k == 1 :
                            weightboard[j+2][i-2] += G33
                            if find33 >= 1 : weightboard[j+2][i-2] -= B33 
            temp = one
            one = zero
            zero = temp

        #122020 120220 대각반대각
        for l in range(2) :
            for k in range(2) :
                for i in range(2, 11) :
                    for j in range(3, 11) : 
                        if board[j-2][i-2] == one and board[j-1][i-1] == counter and board[j][i] == two and board[j+1][i+1] == zero and board[j+2][i+2] == counter and board[j+3][i+3] == zero2 :
                            if l == 0 :
                                weightboard[j+3][i+3] += G33
                                if find33 >= 1 : weightboard[j+3][i+3] -= B33 
                            elif l == 1 :
                                weightboard[j-2][i-2] += G33
                                if find33 >= 1 : weightboard[j-2][i-2] -= B33 
                        if board[j+2][i-2] == one and board[j+1][i-1] == counter and board[j][i] == two and board[j-1][i+1] == zero and board[j-2][i+2] == counter and board[j-3][i+3] == zero2 :
                            if l == 0 :
                                weightboard[j-3][i+3]+= G33
                                if find33 >= 1 : weightboard[j-3][i+3] -= B33 
                            elif l == 1 :
                                weightboard[j+2][i-2] += G33
                                if find33 >= 1 : weightboard[j+2][i-2] -= B33 
                temp = two
                two = zero
                zero = temp
            temp = one
            one = zero2
            zero2 = temp

        return board, weightboard

    #Blocked A33-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def B_A33(self, board_list, weightboard_list) :
        board = np.reshape(board_list, (15,15))
        weightboard = np.reshape(weightboard_list, (15,15))
        zero = 0
        two = counter
        one = computer
        zero2 = 0
        #21110 가로세로
        for k in range(2) :
            for i in range(2,12) :
                for j in range(0,14) :
                    if board[j][i-2] == two and board[j][i-1] == computer and board[j][i] == computer and board[j][i+1] == computer and board[j][i+2] == zero :
                        if k == 0 : weightboard[j][i+2] += AB33
                        elif k == 1 : weightboard[j][i-2] += AB33
                    if board[i-2][j] == two and board[i-1][j] == computer and board[i][j] == computer and board[i+1][j] == computer and board[i+2][j] == zero :
                        if k == 0 : weightboard[i+2][j] += AB33
                        elif k == 1 : weightboard[i-2][j] += AB33
            temp = two
            two = zero
            zero = temp
        #210110 211010 가로세로
        for l in range(2) : 
            for k in range(2) : 
                for i in range(2,11) :
                    for j in range(0,14) :
                        if board[j][i-2] == two and board[j][i-1] == computer and board[j][i] == one and board[j][i+1] == zero and board[j][i+2] == computer and board[j][i+3] == zero2 :
                            if l == 0 :
                                #211010
                                if k == 0: weightboard[j][i+1] += AB33
                                #210110
                                elif k == 1 : weightboard[j][i+3] += AB33
                            if l == 1 :
                                #011012
                                if k == 0 : weightboard[j][i-2] += AB33
                                #010112
                                if k == 1 : weightboard[j][i] += AB33
                        if board[i-2][j] == two and board[i-1][j] == computer and board[i][j] == one and board[i+1][j] == zero and board[i+2][j] == computer and board[i+3][j] == zero2 :
                            if l == 0 :
                                #211010
                                if k == 0 : weightboard[i+1][j] += AB33
                                #210110
                                elif k == 1 : weightboard[i+3][j] += AB33
                            elif l == 1 :
                                #011012
                                if k == 0 : weightboard[i-2][j] += AB33
                                #010112
                                elif k == 1 : weightboard[i][j] += AB33
                temp = one
                one = zero
                zero = temp
            temp = two
            two = zero2
            zero2 = temp

        #21110 대각반대각
        for k in range(2):
            for i in range(2,12) :
                for j in range(2,12) :
                    if board[j-2][i-2] == two and board[j-1][i-1] == computer and board[j][i] == computer and board[j+1][i+1] == computer and board[j+2][i+2] == zero :
                        if k == 0 : weightboard[j+2][i+2] += AB33
                        elif k == 1 : weightboard[j-2][i-2] += AB33
                    if board[j+2][i-2] == two and board[j+1][i-1] == computer and board[j][i] == computer and board[j-1][i+1] == computer and board[j-2][i+2] == zero :
                        if k == 0 : weightboard[j-2][i+2] += AB33
                        elif k == 1 : weightboard[j+2][i-2] += AB33
            temp = two
            two = zero
            zero = temp
        
        #211010 210110 대각반대각
        for l in range(2) :
            for k in range(2) :
                for i in range(3,11) :
                    for j in range(3,11) :
                        if board[j-2][i-2] == two and board[j-1][i-1] == computer and board[j][i] == one and board[j+1][i+1] == zero and board[j+2][i+2] == computer and board[j+3][i+3] == zero2 :
                            if l == 0 :
                                #211010
                                if k == 0: weightboard[j+1][i+1] += AB33
                                #210110
                                elif k == 1 : weightboard[j][i] += AB33
                            elif l == 1 :
                                #011012
                                if k == 0: weightboard[j-2][i-2] += AB33
                                #010112
                                elif k == 1 : weightboard[j][i] += AB33
                        if board[j+2][i-2] == two and board[j+1][i-1] == computer and board[j][i] == one and board[j-1][i+1] == zero and board[j-2][i+2] == computer and board[j-3][i+3] == zero2 :
                            if l == 0:
                                #211010
                                if k ==0 : weightboard[j-1][i+1] += AB33
                                #210110
                                elif k == 1 : weightboard[j-3][i+3] += AB33
                            elif l == 1:
                                #011012
                                if k == 0 :  weightboard[j+2][i-2] += AB33
                                #010112
                                elif k == 1 : weightboard[j][i] += AB33

                temp = one
                zero = one
                one = temp
            temp = two
            zero2 = two
            two = temp
        return board, weightboard


    #Attack 4 ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def A_44(self, board_list, weightboard_list) :
        board = np.reshape(board_list, (15,15))
        weightboard = np.reshape(weightboard_list, (15,15))
        zero = 0
        two = counter
        one = computer
        

        #211110 011112
        for k in range(2) :
            for i in range(2, 11) :
                for j in range(0, 14) :
                    if board[j][i-2] == two and board[j][i-1] == computer and board[j][i] == computer and board[j][i+1] == computer and board[j][i+2] == computer and board[j][i+3] == zero:
                        if k == 0 : weightboard[j][i+3] += A44
                        elif k == 1 : weightboard[j][i-2] += A44
                    if board[i-2][j] == two and board[i-1][j] == computer and board[i][j] == computer and board[i+1][j] == computer and board[i+2][j] == computer and board[i+3][j] == zero :
                        if k == 0 : weightboard[i+3][j] += A44
                        elif k == 1 : weightboard[i-2][j] += A44
            temp = two
            two = zero
            zero = temp
        
        for i in range(2, 11) :
                for j in range(0, 14) :
                    #011110
                    if board[j][i-2] == 0 and board[j][i-1] == computer and board[j][i] == computer and board[j][i+1] == computer and board[j][i+2] == computer and board[j][i+3] == zero:
                        weightboard[j][i+3] += A44
                        weightboard[j][i-2] += A44
                    if board[i-2][j] == 0 and board[i-1][j] == computer and board[i][j] == computer and board[i+1][j] == computer and board[i+2][j] == computer and board[i+3][j] == zero :
                        weightboard[i+3][j] += A44
                        weightboard[i-2][j] += A44

        for i in range(2,12) :
            for j in range(0,14) :
                    #11011
                    if board[j][i-2] == computer and board[j][i-1] == computer and board[j][i] == 0 and board[j][i+1] == computer and board[j][i+2] == computer :
                        weightboard[j][i] += A44
                    if board[i-2][j] == computer and board[i-1][j] == computer and board[i][j] == 0 and board[i+1][j] == computer and board[i+2][j] == computer :
                        weightboard[j][i] += A44

        for k in range(2) :
            for i in range(2,12) :
                for j in range(0,14) :
                    #10111 11101
                    if board[j][i-2] == computer and board[j][i-1] == zero and board[j][i] == computer and board[j][i+1] == one and board[j][i+2] == computer :
                        if k == 0 : weightboard[j][i-1] += A44
                        elif k == 1 : weightboard[j][i+1] += A44
                    if board[i-2][j] == computer and board[i-1][j] == zero and board[i][j] == computer and board[i+1][j] == one and board[i+2][j] == computer :
                        if k == 0 : weightboard[i-1][j] += A44
                        elif k == 1 : weightboard[i+1][j] += A44
            temp = one
            one = zero
            zero = temp

        #211110 011112
        for k in range(2) :
            for i in range(2,11) :
                for j in range(3,11) :
                    if board[j-2][i-2] == two and board[j-1][i-1] == computer and board[j][i] == computer and board[j+1][i+1] == computer and board[j+2][i+2] == computer and board[j+3][i+3] == zero :
                        if k == 0 : weightboard[j+3][i+3] += A44
                        elif k == 1 : weightboard[j-2][i-2] += A44
                    if board[j+2][i-2] == two and board[j+1][i-1] == computer and board[j][i] == computer and board[j-1][i+1] == computer and board[j-2][i+2] == computer and board[j-3][i+3] == zero :
                        if k == 0 : weightboard[j-3][i+3] += A44
                        elif k == 1 : weightboard[j+2][i-2] += A44
            temp = two
            two = zero
            zero = temp

        for i in range(2,11) :
            for j in range(3, 11) :
                #011110
                if board[j-2][i-2] == 0 and board[j-1][i-1] == computer and board[j][i] == computer and board[j+1][i+1] == computer and board[j+2][i+2] == computer and board[j+3][i+3] == 0 :
                    weightboard[j-2][i-2] += A44
                    weightboard[j+3][i+3] += A44
                if board[j+2][i-2] == 0 and board[j+1][i-1] == computer and board[j][i] == computer and board[j-1][i+1] == computer and board[j-2][i+2] == computer and board[j-3][i+3] == 0 :
                    weightboard[j+2][i-2] += A44
                    weightboard[j-3][i+3] += A44

        for i in range(2,12):
            for j in range(2,12) :
                #11011
                if board[j-2][i-2] == computer and board[j-1][i-1] == computer and board[j][i] == 0 and board[j+1][i+1] == computer and board[j+2][i+2] == computer : weightboard[j][i] += A44
                if board[j+2][i-2] == computer and board[j+1][i-1] == computer and board[j][i] == 0 and board[j-1][i+1] == computer and board[j-2][i+2] == computer : weightboard[j][i] += A44

        #10111 11101
        for k in range(2) :
            for i in range(2,12) :
                for j in range (2,12) :
                    if board[j-2][i-2] == computer and board[j-1][i-1] == one and board[j][i] == computer and board[j+1][i+1] == zero and board[j+2][i+2] == computer : 
                        if k == 0 : weightboard[j+1][i+1] += A44
                        elif k == 1 : weightboard[j-1][i-1] += A44
                    if board[j+2][i-2] == computer and board[j+1][i-1] == one and board[j][i] == computer and board[j-1][i+1] == zero and board[j-2][i+2] == computer :
                        if k == 0 : weightboard[j-1][i+1] += A44
                        elif k == 1 : weightboard[j+1][i-1] += A44
        return board, weightboard


    #G 22 -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def G_22(self, board_list, weightboard_list) : 
        board = np.reshape(board_list, (15,15))
        weightboard = np.reshape(weightboard_list, (15,15))
        find22 = 0
       
        #0220
        for i in range(1,12) :
            for j in range(0,14) :
                if board[j][i-1] == 0 and board[j][i] == counter and board[j][i+1] == counter and board[j][i+2] == 0 : 
                    weightboard[j][i-1] += G22
                    weightboard[j][i+2] += G22
                    find22 = find22 + 1
                if board[i-1][j] == 0 and board[i][j] == counter and board[i+1][j] == counter and board[i+2][j] == 0 :
                    weightboard[i-1][j] += G22
                    weightboard[i+2][j] += G22
                    find22 = find22 + 1
        
        for i in range (1, 12) :
            for j in range (2, 12) :
                if board[j-1][i-1] == 0 and board[j][i] == counter and board[j+1][i+1] == counter and board[j+2][i+2] == 0:
                    weightboard[j-1][i-1] += G22
                    weightboard[j+2][i+1] += G22
                    find22 = find22 + 1
                if board[j+1][i-1] == 0 and board[j][i] == counter and board[j-1][i+1] == counter and board[j-2][i+2] == 0:
                    weightboard[j+1][i-1] += G22
                    weightboard[j-2][i+2] += G22
                    find22 = find22 + 1
        return find22


    #Blocked 22 -------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def B_22(self,find22,board_list, weightboard_list) :
        board = np.reshape(board_list, (15,15))
        weightboard = np.reshape(weightboard_list, (15,15))
        zero = 0
        one = computer

        for k in range(2) :
            for i in range(1,12) :
                for j in range(0,14) :
                    if board[j][i-1] == one and board[j][i] == counter and board[j][i+1] == counter and  board[j][i+2] == zero :
                        if k == 0 : 
                            weightboard[j][i+2] += G22
                            if find22 >= 1 : weightboard[j][i+2] -= B22
                        elif k == 1 :
                            weightboard[j][i-1] += G22
                            if find22 >= 1 : weightboard[j][i-1] -= B22
                    if board[i-1][j] == one and board[i][j] == counter and board[i+1][j] == counter and  board[i+2][j] == zero :
                        if k == 0 : 
                            weightboard[i+2][j] += G22
                            if find22 >= 1 : weightboard[i+2][j]-= B22
                        elif k == 1 :
                            weightboard[i-1][j] += G22
                            if find22 >= 1 : weightboard[i-1][j] -= B22
                    
            temp = one
            one = zero
            zero = temp
        
        for k in range(2) :
            for i in range(2,12) :
                for j in range(2,12) :
                    if board[j-1][i-1] == one and board[j][i] == counter and board[j+1][i+1] == counter and  board[j+2][i+2] == zero :
                        if k == 0 : 
                            weightboard[j+2][i+2] += G22
                            if find22 >= 1 : weightboard[j+2][i+2] -= B22
                        elif k == 1 :
                            weightboard[j-1][i-1] += G22
                            if find22 >= 1 : weightboard[j+2][i-1]-= B22
                    if board[j+1][i-1] == one and board[j][i] == counter and board[j-1][i+1] == counter and  board[j-2][i+2] == zero :
                        if k == 0 : 
                            weightboard[j-2][i+2] += G22
                            if find22 >= 1 : weightboard[j-2][i+2] -= B22
                        elif k == 1 :
                            weightboard[j+1][i-1] += G22
                            if find22 >= 1 : weightboard[j+1][i-1]-= B22
            temp = one
            one = zero
            zero = temp
        return board, weightboard


    #Black ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def blackweight(self, board_list, weightboard_list) :
        board = np.reshape(board_list, (15,15))
        weightboard = np.reshape(weightboard_list, (15,15))
        for i in range(board_size) :
            for j in range(board_size) :
                if board[j][i] == BoardState.BLACK :
                    for k in range(-1,1) :
                        for l in range(-1,1) :
                            if board[l][k] == BoardState.EMPTY : weightboard[l][k] += 1
        return board, weightboard


    #White ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def whiteweight(self, board_list, weightboard_list) :
        board = np.reshape(board_list, (15,15))
        weightboard = np.reshape(weightboard_list, (15,15))
        for i in range(board_size) :
            for j in range(board_size) :
                if board[j][i] == BoardState.WHITE :
                    for k in range(-1,1) :
                        for l in range(-1,1) :
                            if board[l][k] == BoardState.EMPTY : weightboard[l][k] -= 1
        return board, weightboard




    def evaluate(self) :
        
        state_vector = []
        weight_vector = []
        for i in range(board_size) :
            for j in range(board_size) :
                state_vector.append(self.__omok.get_board()[i][j])
        for i in range(board_size) :
            for j in range(board_size) :
                weight_vector.append(self.__omok.get_weightboard()[i][j])

        find22 = self.G_22(state_vector,weight_vector)
        (state_vector, weight_vector) = self.B_22(find22,state_vector, weight_vector)
        find33 = self.G_33(state_vector, weight_vector)
        (state_vector, weight_vector) = self.B_G33(find33,state_vector, weight_vector)
        (state_vector, weight_vector) = self.G_44(state_vector, weight_vector)
        (state_vector, weight_vector) = self.A_33(state_vector, weight_vector)
        (state_vector, weight_vector) = self.B_A33(state_vector, weight_vector)
        (state_vector, weight_vector) = self.A_44(state_vector, weight_vector)
        (state_vector, weight_vector) = self.blackweight(state_vector, weight_vector)
        (state_vector, weight_vector) = self.whiteweight(state_vector, weight_vector)
        
        for i in range(board_size):
            for j in range(board_size) :
                evaluate_array.append([weight_vector[j][i],j,i])

        return evaluate_array


    #여기서 tree는 evaluate_array
    def alpha_beta(self, depth, nodeIndex, ai, tree, alpha = 10000000, beta = -1000000) :
        if(depth == 3) : return tree[nodeIndex][0]
        
        #best_I = 0
        #best_J = 0

        if depth % 2 == 0 :
            #최대
            best = alpha     
            for i in range(2) :   
                nextState = counter
                nextPlay = AI(deepcopy(self.__omok),nextState, self.__depth + 1)
                nextPlay.set_board(tree[nodeIndex][1], tree[nodeIndex][2],self.__currentState)
                (val,y,x) = self.alpha_beta(depth+1, nodeIndex*2+1, nextPlay, self.evaluate(), alpha, beta)
                if val < best :
                    best = val
                    (ai.__currentI, ai.__currentJ) = (y,x)
               
                if best < beta :
                    beta = best
                    (ai.__currentI, ai.__currentJ) = (y,x)
               
               # best = min(best,val)
               # beta = min(beta, best)
                if beta<=alpha : break
                i+=1
        else :
            best = beta  
            for i in range(2) :       
                nextState = computer
                nextPlay = AI(deepcopy(self.__omok),nextState, self.__depth + 1)
                nextPlay.set_board(tree[nodeIndex][1], tree[nodeIndex][2],self.__currentState)
                (val,y,x) = self.alpha_beta(depth +1, nodeIndex*2+1, nextPlay, self.evaluate(), alpha, beta)
                if val > best :
                    best = val
                    best_I = y
                    best_J = x
                if best > alpha :
                    alpha = best
                    best_I = y
                    best_J = x

                #best = max(best, val)
                #alpha = max(alpha, best)
                if beta<= alpha : break
                i+=1

        return best_I,best_J
        

    #처음 시작할 때 검은 돌 센터에 두고 시작
    def first(self) :
        self.__omok.check_board((7,7))
        return True

    def one_step(self) :
        for i in range(board_size) :
            for j in range(board_size) :
                if self.__omok.get_board()[i][j] != BoardState.EMPTY : continue  #놓을 수 있는 자리인지 확인
        node = AI(self.__omok, self.__currentState, self.__depth)
        self.alpha_beta(3,0,node,node.evaluate())
        (i,j) = (node.__currentI,node.__currentJ)
        if not i is None and not j is None :
            self.__omok.check_board((i,j))
            return True
        return False


class Omok(object):
    def __init__(self, surface):
        self.board = [[BoardState.EMPTY for i in range(board_size)] for j in range(board_size)]
        self.weightboard = [[0 for i in range(board_size)] for j in range(board_size)]
        self.menu = Menu(surface)
        self.rule = Rule(self.board)
        self.surface = surface
        self.pixel_coords = []
        self.set_coords()
        self.set_image_font()
        self.__board = np.reshape(self.board,(15,15))
        self.__currentI = -1
        self.__currentJ = -1
        self.__currentState = BoardState.EMPTY
        
             

    def init_game(self):
        self.turn  = black_stone
        self.draw_board()
        self.menu.show_msg(empty)
        self.init_board()
        self.coords = []
        self.redos = []
        self.id = 1
        self.is_show = True
        self.is_gameover = False
        self.is_forbidden = False

        

    def set_image_font(self):
        white_img = pygame.image.load('image/white.png')
        self.white_img = pygame.transform.scale(white_img, (grid_size, grid_size))
        black_img = pygame.image.load('image/black.png')
        self.black_img = pygame.transform.scale(black_img, (grid_size, grid_size))
        self.last_w_img = pygame.image.load('image/white_a.png')
        self.last_b_img = pygame.image.load('image/black_a.png')
        self.board_img = pygame.image.load('image/board.png')
        self.font = pygame.font.Font("freesansbold.ttf", 14)

    def init_board(self):
        for y in range(board_size):
            for x in range(board_size):
                self.board[y][x] = 0

    def draw_board(self):
        self.surface.blit(self.board_img, (0, 0))

    def draw_image(self, img_index, x, y):
        img = [self.black_img, self.white_img, self.last_b_img, self.last_w_img]
        self.surface.blit(img[img_index], (x, y))

    def show_number(self, x, y, stone, number):
        colors = [None, white, black, red, red]
        color = colors[stone]
        self.make_text(self.font, str(number), color, x + 15, y + 15, 'center')

    def hide_numbers(self):
        for i in range(len(self.coords)):
            x, y = self.coords[i]
            self.draw_image(i % 2, x, y)
        if self.coords:
            x, y = self.coords[-1]
            self.draw_image(i % 2 + 2, x, y)

    def show_numbers(self):
        stone = 1
        i = -1
        for i in range(len(self.coords) - 1):
            x, y = self.coords[i]
            self.show_number(x, y, stone, i + 1)
            stone = 3 - stone
        if self.coords:
            x, y = self.coords[-1]
            self.draw_image(stone - 1, x, y)
            self.show_number(x, y, stone + 2, i + 2)
        
    def undo(self):
        if not self.coords:
            return            
        self.id -= 1
        self.draw_board()
        coord = self.coords.pop()
        self.redos.append(coord)
        x, y = self.get_point(coord)
        self.board[y][x] = empty
        if self.is_show:
            self.hide_numbers()
            self.show_numbers()
        else:
            self.hide_numbers()
        self.turn = 3 - self.turn

    def change_state(self) :
        if self.turn == BoardState.BLACK: self.turn = BoardState.WHITE
        else : self.turn = BoardState.BLACK

    def turn_change(self):
        if computer == BoardState.BLACK : 
            computer = BoardState.WHITE
            counter = BoardState.BLACK
        else : 
            computer = BoardState.WHITE
            counter = BoardState.BLACK

    def make_text(self, font, text, color, x, y, position):
        surf = font.render(text, False, color)
        rect = surf.get_rect()
        if position == 'center':
            rect.center = (x, y)
        else:
            rect.midright = (x, y)
        self.surface.blit(surf, rect)

    def set_coords(self):
        for y in range(board_size):
            for x in range(board_size):
                self.pixel_coords.append((x * grid_size + 25, y * grid_size + 25))

    def get_coord(self, pos):
        for coord in self.pixel_coords:
            x, y = coord
            rect = pygame.Rect(x, y, grid_size, grid_size)
            if rect.collidepoint(pos):
                return coord
        return None

    def get_point(self, coord):
        x, y = coord
        x = (x - 25) // grid_size
        y = (y - 25) // grid_size
        return x, y

    def get_board(self) :
        return self.board
    def get_weightboard(self) :
        return self.weightboard

    def set_board(self,i,j,state,) : 
        self.__board[j][i] = state
        self.__currentI = i
        self.__currentJ = j
        self.__currentState = state

    def check_board(self, pos):
        coord = self.get_coord(pos)
        if not coord:
            return False

        x, y = self.get_point(coord)
        if self.board[y][x] != empty:
            return True
        else:
            return self.draw_stone(x, y, coord)
    
    def check_forbidden(self):
        if self.turn == black_stone:
            coords = self.rule.get_forbidden_points(self.turn)
            while coords:
                x, y = coords.pop()
                x, y = x * grid_size + 25, y * grid_size + 25
                self.draw_image(4, x, y)
            self.is_forbidden = True

    def draw_stone(self, coord, stone, increase):
        if self.is_forbidden:
            self.draw_board()
        x, y = self.get_point(coord)
        self.board[y][x] = stone
        self.hide_numbers()
        if self.is_show:
            self.show_numbers()
        self.id += increase
        self.turn = 3 - self.turn
        self.check_forbidden()

    def get_board_result(self) :
        rule = Rule(self.get_board())
        if rule.is_five(self.__currentJ,self.__currentI,self.__currentState) :
            return self.__currentState
        else :
            return BoardState.EMPTY

    

    def check_gameover(self, coord):
        x, y = self.get_point(coord)
        if self.id == board_size * board_size:
            self.menu.show_msg(tie)
            return True
        elif 5 <= self.rule.is_gameover(x, y, self.turn):
            self.menu.show_msg(self.turn)
            return True
        return False

        
class Menu(object):
    def __init__(self, surface):
        self.font = pygame.font.Font('freesansbold.ttf', 20)
        self.surface = surface
        self.draw_menu()

    def draw_menu(self):
        top, left = window_height - 30, window_width - 200
        self.new_rect = self.make_text(self.font, 'New Game', blue, None, top - 60, left)
        self.quit_rect = self.make_text(self.font, 'Quit Game', blue, None, top - 30, left)
        self.undo_rect = self.make_text(self.font, 'Undo', blue, None, top - 150, left)
        self.turn_rect = self.make_text(self.font, 'White', blue, None, top - 120, left)
        self.doublethree_rect = self.make_text(self.font, '33Ban', blue, None, top- 90, left)


    def show_msg(self, msg_id):
        msg = {
            empty : '                                    ',
            black_stone: 'Black win!!!',
            white_stone: 'White win!!!',
            tie: 'Tie',
        }
        center_x = window_width - (window_width - board_width) // 2
        self.make_text(self.font, msg[msg_id], blue, bg_color, 30, center_x, 1)

    def make_text(self, font, text, color, bgcolor, top, left, position = 0):
        surf = font.render(text, False, color, bgcolor)
        rect = surf.get_rect()
        if position:
            rect.center = (left, top)
        else:    
            rect.topleft = (left, top)
        self.surface.blit(surf, rect)
        return rect

    def show_hide(self, omok):
        top, left = window_height - 90, window_width - 200
        if omok.is_show:
            self.make_text(self.font, 'Show Number', blue, bg_color, top, left)
            omok.hide_numbers()
            omok.is_show = False
        else:
            self.make_text(self.font, 'Hide Number  ', blue, bg_color, top, left)
            omok.show_numbers()
            omok.is_show = True

    def check_rect(self, pos, omok):
        if self.new_rect.collidepoint(pos):
            return True
        elif self.undo_rect.collidepoint(pos):
            omok.undo()
        elif self.turn_rect.collidepoint(pos):
            omok.turn_change()
        elif self.doublethree_rect.collidepoint(pos):
            omok.redo()
        elif self.quit_rect.collidepoint(pos):
            self.terminate()
        return False
    
    def terminate(self):
        pygame.quit()
        sys.exit()

    def is_continue(self, omok):
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.terminate()
                elif event.type == MOUSEBUTTONUP:
                    if (self.check_rect(event.pos, omok)):
                        return
            pygame.display.update()
              

if __name__ == '__main__':
    main()
