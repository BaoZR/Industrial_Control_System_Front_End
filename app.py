import typing
import time
import math
import traceback
import os
import json
import socket
import threading


from PyQt5.QtCore import Qt, QRectF, QSize, QObject,pyqtSignal, QMimeData, QPoint, QPointF, QRect, QLineF, QLine, QTimer, QEvent, QRect, QAbstractTableModel,QModelIndex
from PyQt5.QtGui import QPen, QBrush, QColor, QResizeEvent,QMouseEvent, QDrag, QPainter, QPixmap, QImage, QPainterPath, QPolygonF, QPolygon, QFont, QFontMetrics, QPainterPathStroker, QTransform, QKeyEvent, QDropEvent,QColorConstants,QIcon
from PyQt5.QtWidgets import (QApplication, QGraphicsView, QGraphicsScene,
                               QGraphicsItem, QGraphicsRectItem, QMainWindow,
                               QVBoxLayout, QWidget, QLabel,QGraphicsItemGroup,QGraphicsTextItem,QGraphicsPixmapItem,QGraphicsLineItem,QGraphicsSimpleTextItem,QGraphicsEllipseItem,QHBoxLayout,QVBoxLayout,QTableWidgetItem, QSplitter, QTableWidget, QHeaderView,QGridLayout,QTableView,QAction,QFileDialog)

image_list = [
    ["gas-meter","hydrant"],
    ["temp-meter","water-meter"],
    ["water-valve","wind-meter"],
    ["rectangle","line"],
    ["ellipse","text"]
]
pic_folder_path = "./images/"
pic_suffix = ".png"
open_icon_path = "./images/action/open.png"
save_icon_path = "./images/action/save.png"
delete_icon_path = "./images/action/delete.png"
clear_icon_path = "./images/action/clear.png"
edit_icon_path = "./images/action/edit.png"
watch_icon_path = "./images/action/watch.png"
suffix =".gkqd"
filter_str = "工控系统前端(*" + suffix +")"
default_color_name = "black"
white_color = QColor(255,255,255,255)
black_color = QColor(0,0,0,255)
server_port = 5005
server_address = "127.0.0.1"
device_type_sn_list = ["gas-meter","temp-meter","wind-meter","water-meter"]


class MySignal(QObject):
    set_table_properties_signal = pyqtSignal(QGraphicsItem)
    clear_table_properties_signal = pyqtSignal()
    update_mypicture_signal = pyqtSignal(str)

my_signal = MySignal()

def is_valid_color_name(color_name:str)->bool:
    """ Check if a color name is valid. """
    color_name = color_name.capitalize()
    color_list = [attr for attr in dir(QColorConstants) if   not attr.startswith("__")  and not callable(getattr(QColorConstants, attr))]
    if color_name in color_list:
        return True
    return False

def is_valid_color_value(r:int,g:int,b:int,a:int)->bool:
    """ Check if a color value is valid. """
    if int(r) >= 0 and int(r) <= 255 and int(g) >= 0 and int(g) <= 255 and int(b) >= 0 and int(b) <= 255 and int(a) >= 0 and int(a) <= 255:
        return True
    return False

def get_p2_from_p1(p1:QPointF, length:float, angle:float)->QPointF:
    dx = 0
    dy = 0
    if angle == 0:
        dx = length
    elif angle < 90 and angle > 0:
        dx = length * math.cos(math.radians(angle))
        dy = -length * math.sin(math.radians(angle))
    elif angle == 90:
        dy = -length
    elif angle < 180 and angle > 90:
        dx = length * math.cos(math.radians(angle))
        dy = -length * math.sin(math.radians(angle))
    elif angle == 180:
        dx = -length
    elif angle < 270 and angle > 180:
        dx = length * math.cos(math.radians(angle))
        dy = -length * math.sin(math.radians(angle))
    elif angle == 270:
        dy = length
    elif angle < 360 and angle > 270:
        dx = length * math.cos(math.radians(angle))
        dy = -length * math.sin(math.radians(angle))
        #print(dx,dy)
    return QPointF(p1.x() + dx, p1.y() + dy)

class DragLabel(QLabel):

    def mouseMoveEvent(self, e:QMouseEvent):

        if e.buttons() != Qt.MouseButton.LeftButton:
            return

        mimeData = QMimeData()

        drag = QDrag(self)
        drag.setMimeData(mimeData)

        drag.exec(Qt.DropAction.MoveAction)

class MyPictureItem(QGraphicsItemGroup):
    def __init__(self, 
                 pic_name,
                 text = "",
                 #pos = QPointF(0,0),
                 icon_width = 40,
                 text_relevate_pos = QPoint(40,10),
                 text_width = 50,
                 zValue = 0,
                 ):
        super().__init__()
        self.pic_name = pic_name
        self.pic_name_path = pic_folder_path + pic_name + pic_suffix
        pm = QPixmap(self.pic_name_path).scaledToWidth(icon_width,Qt.TransformationMode.SmoothTransformation)
        self.setPos(QPointF(0,0))
        self.picItem = MyGraphicsPixmapItem(pm)
        self.picItem.setPos(0,0)
        self.picItem.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)

        self.textItem:QGraphicsTextItem = QGraphicsTextItem()
        self.textItem.setTextWidth(text_width)
        self.textItem.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)
        self.textItem.setPos(text_relevate_pos.x(),text_relevate_pos.y())
        self.setZValue(zValue)

        self.addToGroup(self.picItem)
        self.addToGroup(self.textItem)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)

        self.device_sn = None
        if pic_name in device_type_sn_list:
            self.device_sn = ""

        self.textItem.setPlainText(MyPictureItem.get_chinese_name(pic_name))

    def keyPressEvent(self, event:QKeyEvent):

        x = self.x()
        y = self.y()

        key = event.key()
        if(key == Qt.Key.Key_Down):
            y = y + 1  
        elif(key == Qt.Key.Key_Up):
            y = y - 1
        elif(key == Qt.Key.Key_Left):
            x = x - 1
        elif(key == Qt.Key.Key_Right):
            x = x + 1
        elif(key == Qt.Key.Key_Delete):
            self.scene().removeItem(self)
            #print("view keyPressEvent")
            
        self.setPos(x,y)

        return super().keyPressEvent(event)
        
    def to_dict(self)->dict:
        """ Convert the item to a dictionary. """
        d = {
            "type":"MyPictureItem",
            "pic_name": self.pic_name,
            "pos": [self.pos().x(),self.pos().y()],
            "icon_width": self.picItem.pixmap().width(),
            "text": self.textItem.toPlainText(),
            "zValue": self.zValue()
        }
        if self.device_sn is not None and self.pic_name in device_type_sn_list:
            d["device_sn"] = self.device_sn
        return d

    def from_dict(self, d:dict)->None:


        pass

    @staticmethod
    def get_chinese_name(s : str)->str:
        text = "未定义"
        if s == "gas-meter":
            text = "气体检测"
        elif s == "temp-meter":
            text = "温度计"
        elif s == "wind-meter":
            text = "风速计"
        elif s == "water-meter":
            text = "水流量计"
        elif s == "hydrant":
            text = "水泵"
        elif s == "water-valve":
            text = "阀门"

        return text

class MyGraphicsPixmapItem(QGraphicsPixmapItem):
    def keyPressEvent(self, event:QKeyEvent):

        x = self.x()
        y = self.y()

        key = event.key()
        if(key == Qt.Key.Key_Down):
            y = y + 1  
        elif(key == Qt.Key.Key_Up):
            y = y - 1
        elif(key == Qt.Key.Key_Left):
            x = x - 1
        elif(key == Qt.Key.Key_Right):
            x = x + 1
        elif(key == Qt.Key.Key_Delete):
            self.scene().removeItem(self)

        self.setPos(x,y)
        return super().keyPressEvent(event)
    
    def sceneEvent(self, event:QEvent):
        if event.type() == QEvent.Type.MouseButtonPress:
            print("press event")
            return True
        return False
    
    def setPixmap(self, pixmap):
        return super().setPixmap(pixmap)

class MyGraphicsRectItem(QGraphicsRectItem):
    def __init__(self,
                 pos = QPointF(0,0),
                 rectSize = QRectF(0,0,100,80),
                 rectPen = QPen(black_color, 4),
                 rectBrush = QBrush(white_color),
                 zValue = 0
                 ):
        super().__init__()
        self.setPos(pos)
        self.setRect(rectSize)
        self.setPen(rectPen)
        self.setBrush(rectBrush)
        self.setZValue(zValue)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)
        self.selected_edge = None
        self.click_pos = self.click_rect = None

    def mousePressEvent(self, event):
        """ The mouse is pressed, start tracking movement. """
        #print('mousePress')
        self.click_pos = event.pos()
        rect = self.rect()
        if abs(rect.top() - self.click_pos.y()) < 5 and abs(rect.left() - self.click_pos.x()) < 5:
            self.selected_edge = 'topleft'
        elif abs(rect.top() - self.click_pos.y()) < 5 and abs(rect.right() - self.click_pos.x()) < 5:
            self.selected_edge = 'topright'
        elif abs(rect.bottom() - self.click_pos.y()) < 5 and abs(rect.left() - self.click_pos.x()) < 5:
            self.selected_edge = 'bottomleft'
        elif abs(rect.bottom() - self.click_pos.y()) < 5 and abs(rect.right() - self.click_pos.x()) < 5:
            self.selected_edge = 'bottomright'
        elif abs(rect.left() - self.click_pos.x()) < 5:
            self.selected_edge = 'left'
        elif abs(rect.right() - self.click_pos.x()) < 5:
            self.selected_edge = 'right'
        elif abs(rect.top() - self.click_pos.y()) < 5:
            self.selected_edge = 'top'
        elif abs(rect.bottom() - self.click_pos.y()) < 5:
            self.selected_edge = 'bottom'

        else:
            self.selected_edge = None
        
        self.click_pos = event.pos()
        self.click_rect = rect
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):

        flags = self.flags()
        if ((flags & QGraphicsItem.GraphicsItemFlag.ItemIsMovable) != QGraphicsItem.GraphicsItemFlag.ItemIsMovable):
             return super().mouseMoveEvent(event)  

        """ Continue tracking movement while the mouse is pressed. """
        # Calculate how much the mouse has moved since the click.
        pos = event.pos()
        x_diff = pos.x() - self.click_pos.x()
        y_diff = pos.y() - self.click_pos.y()

        # Start with the rectangle as it was when clicked.
        rect = QRectF(self.click_rect)

        # Then adjust by the distance the mouse moved.
        if self.selected_edge is None:
            rect.translate(x_diff, y_diff)
        elif self.selected_edge == 'topleft':
            rect.adjust(x_diff, y_diff, 0, 0)
        elif self.selected_edge == 'topright':
            rect.adjust(0, y_diff, x_diff, 0)
        elif self.selected_edge == 'bottomleft':
            rect.adjust(x_diff, 0, 0, y_diff)
        elif self.selected_edge == 'bottomright':
            rect.adjust(0, 0, x_diff, y_diff)
        elif self.selected_edge == 'top':
            rect.adjust(0, y_diff, 0, 0)
        elif self.selected_edge == 'left':
            rect.adjust(x_diff, 0, 0, 0)
        elif self.selected_edge == 'bottom':
            rect.adjust(0, 0, 0, y_diff)
        elif self.selected_edge == 'right':
            rect.adjust(0, 0, x_diff, 0)

        #print(self.selected_edge)

        # Also check if the rectangle has been dragged inside out.

        
        if rect.width() < 5:
            if self.selected_edge == 'left' or self.selected_edge == 'topleft' or self.selected_edge == "bottomleft":
                rect.setLeft(rect.right() - 5)
            elif self.selected_edge == 'right' or self.selected_edge == "topright" or self.selected_edge == "bottomright":
                rect.setRight(rect.left() + 5)
            
        if rect.height() < 5:
            if self.selected_edge == 'top' or self.selected_edge == "topleft" or self.selected_edge == "topright":
                rect.setTop(rect.bottom() - 5)
            elif self.selected_edge == 'bottom' or self.selected_edge == "bottomleft" or self.selected_edge == "bottomright":
                rect.setBottom(rect.top() + 5)
        

        # Finally, update the rect that is now guaranteed to stay in bounds.
        self.setRect(rect)

    def hoverMoveEvent(self, event):
        #print('hoverMove')
        self.hover_pos = event.pos()
        rect = self.rect()
        cursor_shape = Qt.CursorShape.ArrowCursor
        
        #corner is not need to be hovered
        if abs(rect.left() - self.hover_pos.x()) < 5 and abs(rect.top() - self.hover_pos.y()) < 5:
            cursor_shape = Qt.CursorShape.SizeFDiagCursor
        elif abs(rect.right() - self.hover_pos.x()) < 5 and abs(rect.top() - self.hover_pos.y()) < 5:
            cursor_shape = Qt.CursorShape.SizeBDiagCursor
        elif abs(rect.left() - self.hover_pos.x()) < 5 and abs(rect.bottom() - self.hover_pos.y()) < 5:
            cursor_shape = Qt.CursorShape.SizeBDiagCursor
        elif abs(rect.right() - self.hover_pos.x()) < 5 and abs(rect.bottom() - self.hover_pos.y()) < 5:
            cursor_shape = Qt.CursorShape.SizeFDiagCursor
        elif abs(rect.left() - self.hover_pos.x()) < 5:
            cursor_shape = Qt.CursorShape.SizeHorCursor
        elif abs(rect.right() - self.hover_pos.x()) < 5:
            cursor_shape = Qt.CursorShape.SizeHorCursor
        elif abs(rect.top() - self.hover_pos.y()) < 5:
            cursor_shape = Qt.CursorShape.SizeVerCursor
        elif abs(rect.bottom() - self.hover_pos.y()) < 5:
            cursor_shape = Qt.CursorShape.SizeVerCursor        
        else:
            #self.selected_edge = None
            cursor_shape = Qt.CursorShape.ArrowCursor
        self.setCursor(cursor_shape)

        return super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        #print('hoverLeave')
        #self.selected_edge = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        return super().hoverLeaveEvent(event)

    def keyPressEvent(self, event:QKeyEvent):

        x = self.x()
        y = self.y()

        key = event.key()
        if(key == Qt.Key.Key_Down):
            y = y + 1  
        elif(key == Qt.Key.Key_Up):
            y = y - 1
        elif(key == Qt.Key.Key_Left):
            x = x - 1
        elif(key == Qt.Key.Key_Right):
            x = x + 1
        elif(key == Qt.Key.Key_Delete):
            self.scene().removeItem(self)

        self.setPos(x,y)
        return super().keyPressEvent(event)

    def to_dict(self)->dict:
        """ Convert the item to a dictionary. """
        return {
            "type":"MyGraphicsRectItem",
            "pos": [self.pos().x(),self.pos().y()],
            "rect":[self.rect().x(),self.rect().y(),self.rect().width(),self.rect().height()],
            "pen_color":[self.pen().color().red(),self.pen().color().green(),self.pen().color().blue(),self.pen().color().alpha()],
            "pen_width":self.pen().width(),
            "brush_color":[self.brush().color().red(),self.brush().color().green(),self.brush().color().blue(),self.brush().color().alpha()],
            "zValue": self.zValue()
        }

class MyGraphicsLineItem(QGraphicsLineItem):
    def __init__(self,
                 pos = QPointF(0,0),
                 start = QPoint(10, 10),
                 pen = QPen(black_color, 4),
                 length = 100,
                 angle = 45,
                 zValue = 0
                 ):
        super().__init__()
        end = get_p2_from_p1(start, length, angle)
        self.setPos(pos)
        self.setPen(pen)
        self.setLine(start.x(), start.y(), end.x(), end.y())
        self.setZValue(zValue)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)
        self.setAcceptHoverEvents(True)
        
        self.selected_point = None
        self.click_pos = None
        self.click_line = None

    def mousePressEvent(self, event):

        self.click_pos = event.pos()
        line = self.line()
        self.click_line = self.line()
        x1, y1, x2, y2 = line.x1(), line.y1(), line.x2(), line.y2()
        if abs(event.pos().x() - x1) < 5 and abs(event.pos().y() - y1) < 5:
            self.selected_point = 'x1'
        elif abs(event.pos().x() - x2) < 5 and abs(event.pos().y() - y2) < 5:
            self.selected_point = 'x2'
        else:
            self.selected_point = None

            
        return super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.selected_point = None
        return super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        
        flags = self.flags()
        if ((flags & QGraphicsItem.GraphicsItemFlag.ItemIsMovable) != QGraphicsItem.GraphicsItemFlag.ItemIsMovable):
             return super().mouseMoveEvent(event)

        pos = event.pos()
        x_diff = pos.x() - self.click_pos.x()
        y_diff = pos.y() - self.click_pos.y()
        line = QLineF(self.click_line)

        if self.selected_point is None:
            line.translate(x_diff, y_diff)
        elif self.selected_point == 'x1':
            line.setP1(pos)
        elif self.selected_point == 'x2':
            line.setP2(pos)

        #print(self.selected_point)
        self.setLine(line)

    def hoverMoveEvent(self, event):
        self.hover_pos = event.pos()
        x1, y1, x2, y2 = self.line().x1(), self.line().y1(), self.line().x2(), self.line().y2()
        cursor_shape = Qt.CursorShape.ArrowCursor
        if abs(self.hover_pos.x() - x1) < 5 and abs(self.hover_pos.y() - y1) < 5:
            #print("hover x1 " + str(self.hover_pos.x()) + " " + str(self.hover_pos.y()) + " " + str(x1) + " " + str(y1))
            cursor_shape = Qt.CursorShape.SizeAllCursor
        elif abs(self.hover_pos.x() - x2) < 5 and abs(self.hover_pos.y() - y2) < 5:
            cursor_shape = Qt.CursorShape.SizeAllCursor
            #print("hover x1 " + str(self.hover_pos.x()) + " " + str(self.hover_pos.y()) + " " + str(x1) + " " + str(y1))
        else:
            cursor_shape = Qt.CursorShape.ArrowCursor
        self.setCursor(cursor_shape)
        return super().hoverMoveEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        return super().hoverLeaveEvent(event)
    
    def keyPressEvent(self, event:QKeyEvent):
        x1 = self.line().x1()
        y1 = self.line().y1()
        x2 = self.line().x2()
        y2 = self.line().y2()

        key = event.key()
        if(key == Qt.Key.Key_Down):
            y1 = y1 + 1  
            y2 = y2 + 1
        elif(key == Qt.Key.Key_Up):
            y1 = y1 - 1
            y2 = y2 - 1
        elif(key == Qt.Key.Key_Left):
            x1 = x1 - 1  
            x2 = x2 - 1
        elif(key == Qt.Key.Key_Right):
            x1 = x1 + 1  
            x2 = x2 + 1
        elif(key == Qt.Key.Key_Delete):
            self.scene().removeItem(self)

        self.setLine(x1,y1,x2,y2)
        return super().keyPressEvent(event)

    def to_dict(self)->dict:
        """ Convert the item to a dictionary. """
        return {
            "type":"MyGraphicsLineItem",
            "pos": [self.pos().x(), self.pos().y()],
            "start": [self.line().x1(), self.line().y1()],
            "pen_width":self.pen().width(),
            "pen_color":[self.pen().color().red(),self.pen().color().green(),self.pen().color().blue(),self.pen().color().alpha()],
            "length":self.line().length(),
            "angle":self.line().angle(),
            "zValue": self.zValue()
        }

class MyGraphicsSimpleTextItem(QGraphicsSimpleTextItem):
    
    def __init__(self,
                 pos = QPointF(0,0),
                 word = "待填入",
                 input_text_color = "red",
                 font = QFont("微软雅黑", 12, 40),
                 zValue = 0
                 ):
        super().__init__()
        self.setPos(pos)
        self.text_color_name = default_color_name
        color = QColor(self.text_color_name)
        if is_valid_color_name(input_text_color):
            self.text_color_name = input_text_color
            color =  QColor(self.text_color_name)

        self.setText(word)
        self.setBrush(color)
        self.setFont(font)
        self.setZValue(zValue)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)

        pass

    def keyPressEvent(self, event:QKeyEvent):
        x = self.x()
        y = self.y()

        key = event.key()
        if(key == Qt.Key.Key_Down):
            y = y + 1  
        elif(key == Qt.Key.Key_Up):
            y = y - 1
        elif(key == Qt.Key.Key_Left):
            x = x - 1
        elif(key == Qt.Key.Key_Right):
            x = x + 1
        elif(key == Qt.Key.Key_Delete):
            self.scene().removeItem(self)

        self.setPos(x,y)
        return super().keyPressEvent(event)

    def to_dict(self)->dict:
        """ Convert the item to a dictionary. """
        return {
            "type":"MyGraphicsSimpleTextItem",
            "pos": [self.pos().x(), self.pos().y()],
            "text": self.text(),
            "text_color": self.text_color_name,
            "font_family": self.font().family(),
            "font_size": self.font().pointSize(),
            "font_weight": self.font().weight(),
            "zValue": self.zValue()
        }

class MyGraphicsEllipseItem(QGraphicsEllipseItem):
    def __init__(self,
                 pos = QPointF(0,0),
                 rect = QRectF(0, 0, 100, 50),
                 pen = QPen(black_color, 4),
                 brush = QBrush(white_color),
                 zValue = 0
                 ):
        super().__init__()
        self.setPos(pos)
        self.setRect(rect)
        self.setPen(pen)
        self.setBrush(brush)
        self.setZValue(zValue)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)
        self.setAcceptHoverEvents(True)

        self.selected_point = None
        self.click_pos = None
        self.click_ellipse = None

    def mousePressEvent(self, event):
        self.click_pos = event.pos()      
        rect = self.rect()
        x , y , w, h = rect.x(), rect.y(), rect.width(), rect.height()
        top = QPointF(x + w/2, y)
        right = QPointF(x + w, y + h/2)
        bottom = QPointF(x + w/2, y + h)
        left = QPointF(x, y + h/2)

        if abs(self.click_pos.x() - top.x()) < 5 and abs(self.click_pos.y() - top.y()) < 5:
            self.selected_point = 'top'
           # print("top")
        elif abs(self.click_pos.x() - right.x()) < 5 and abs(self.click_pos.y() - right.y()) < 5:
            self.selected_point = 'right'
        elif abs(self.click_pos.x() - bottom.x()) < 5 and abs(self.click_pos.y() - bottom.y()) < 5:
            self.selected_point = 'bottom'
        elif abs(self.click_pos.x() - left.x()) < 5 and abs(self.click_pos.y() - left.y()) < 5:
            self.selected_point = 'left'
        else:
            self.selected_point = None

        self.click_ellipse = self.rect()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        
        flags = self.flags()
        if ((flags & QGraphicsItem.GraphicsItemFlag.ItemIsMovable) != QGraphicsItem.GraphicsItemFlag.ItemIsMovable):
             return super().mouseMoveEvent(event)
        
        pos = event.pos()
        x_diff = pos.x() - self.click_pos.x()
        y_diff = pos.y() - self.click_pos.y()
        #print("x_diff:" + str(x_diff) , "y_diff:" + str(y_diff))    
        rect = QRectF(self.click_ellipse)

        if self.selected_point == None:
            rect.translate(x_diff, y_diff)
        elif self.selected_point == 'top':
            rect.adjust(0,y_diff,0,0)
        elif self.selected_point == 'right':
            rect.adjust(0,0,x_diff,0)
        elif self.selected_point == 'bottom':
            rect.adjust(0,0,0,y_diff)
        elif self.selected_point == 'left':
            rect.adjust(x_diff,0,0,0)

        self.setRect(rect)
        #print(rect.x(), rect.y(), rect.width(), rect.height())
        #return super().mouseMoveEvent(event) #这句话不能加

    def hoverMoveEvent(self, event):
        pos = event.pos()
        rect = self.rect()
        x , y , w, h = rect.x(), rect.y(), rect.width(), rect.height()
        top = QPointF(x + w/2, y)
        right = QPointF(x + w, y + h/2)
        bottom = QPointF(x + w/2, y + h)
        left = QPointF(x, y + h/2)
        cursor_shape = Qt.CursorShape.ArrowCursor

        if abs(pos.x() - top.x()) < 5 and abs(pos.y() - top.y()) < 5:
            cursor_shape = Qt.CursorShape.SizeVerCursor
        elif abs(pos.x() - right.x()) < 5 and abs(pos.y() - right.y()) < 5:
            cursor_shape = Qt.CursorShape.SizeHorCursor
        elif abs(pos.x() - bottom.x()) < 5 and abs(pos.y() - bottom.y()) < 5:
            cursor_shape = Qt.CursorShape.SizeVerCursor
        elif abs(pos.x() - left.x()) < 5 and abs(pos.y() - left.y()) < 5:
            cursor_shape = Qt.CursorShape.SizeHorCursor
        else:
            cursor_shape = Qt.CursorShape.ArrowCursor

        self.setCursor(cursor_shape)
        return super().hoverMoveEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        return super().hoverLeaveEvent(event)
  
    def keyPressEvent(self, event:QKeyEvent):
        x = self.x()
        y = self.y()

        key = event.key()
        if(key == Qt.Key.Key_Down):
            y = y + 1  
        elif(key == Qt.Key.Key_Up):
            y = y - 1
        elif(key == Qt.Key.Key_Left):
            x = x - 1
        elif(key == Qt.Key.Key_Right):
            x = x + 1
        elif(key == Qt.Key.Key_Delete):
            self.scene().removeItem(self)

        self.setPos(x,y)
        return super().keyPressEvent(event)

    def to_dict(self)->dict:
        """ Convert the item to a dictionary. """
        return {
            "type":"MyGraphicsEllipseItem",
            "pos": [self.pos().x(), self.pos().y()],
            "rect":[self.rect().x(),self.rect().y(),self.rect().width(),self.rect().height()],
            "pen_color":[self.pen().color().red(),self.pen().color().green(),self.pen().color().blue(),self.pen().color().alpha()],
            "pen_width":self.pen().width(),
            "brush_color":[self.brush().color().red(),self.brush().color().green(),self.brush().color().blue(),self.brush().color().alpha()],
            "zValue": self.zValue()
        }

class MyTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.data = []
        self.pointer = None
        self.table_structure = {
            "rect":("rect_width","rect_height","fill_color","line_width","line_color","zValue"),
            "ellipse":("ellipse_width","ellipse_height","fill_color","line_width","line_color","zValue"),
            "line":("line_width","line_color","line_length","rotate_angle","zValue"),
            "pic":("pic_location","pic_width","text_location","text_width","zValue","device_sn"),
            "text":("text_content","text_color","text_size","text_font","text_weight","zValue","zValue")
        }

    def rowCount(self, parent= QModelIndex()):
        return len(self.data)
    
    def columnCount(self, parent=QModelIndex()):
        return 2
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.data)):
            return None
        if role == Qt.ItemDataRole.DisplayRole  or role == Qt.ItemDataRole.EditRole:
            return self.data[index.row()][index.column()]
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
 
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section == 0:
                    return "属性"
                elif section == 1:
                    return "值"
        return None
    
    def flags(self, index):
        if index.column() == 0:
            return Qt.ItemFlag.ItemIsEnabled
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable 
    
    def setData(self, index:QModelIndex, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.EditRole:
            row, col  = index.row(), index.column()
            self.update_source(row, col, value)
            return True
        return False
    
    def set_source(self, pointer):
        self.pointer = pointer
        if self.pointer is None:
            self.data = []
        elif isinstance(self.pointer, MyPictureItem):
            item: MyPictureItem = self.pointer
            x = str(int(item.x()))
            y = str(int(item.y()))
            rect = item.boundingRect()
            pic: MyGraphicsPixmapItem = item.picItem
            text: MyGraphicsSimpleTextItem = item.textItem 
            text_x = str(int(text.x()))
            text_y = str(int(text.y()))
            device_sn = item.device_sn
            
            self.data = [
                ["图标位置", x + "," + y ],
                ["图标宽度", str(pic.pixmap().width())],
                ["文字位置", text_x + "," + text_y],
                ["文字宽度", str(text.boundingRect().width())],
                ["zValue",  str(item.zValue())]
            ]
            if device_sn is not None and item.pic_name in device_type_sn_list:
                self.data.append(["设备编号", device_sn])

        elif isinstance(self.pointer, MyGraphicsRectItem):
            item: MyGraphicsRectItem = self.pointer
            width = item.rect().width()
            height = item.rect().height()
            fill_color = item.brush().color()
            line_width = item.pen().width()
            line_color = item.pen().color()
            zValue = item.zValue()

            self.data = [
                ["矩形宽度", str(int(width))],
                ["矩形高度", str(int(height))],
                ["填充颜色", f"{fill_color.red()},{fill_color.green()},{fill_color.blue()},{fill_color.alpha()}"],
                ["线条宽度", str(line_width)],
                ["线条颜色", f"{line_color.red()},{line_color.green()},{line_color.blue()},{line_color.alpha()}"],
                ["zValue",  str(zValue)]
            ]

        elif isinstance(self.pointer, MyGraphicsEllipseItem):
            item: MyGraphicsEllipseItem = self.pointer
            width = item.rect().width()
            height = item.rect().height()
            fill_color = item.brush().color()
            line_width = item.pen().width()
            line_color = item.pen().color()
            zValue = item.zValue()

            self.data = [
                ["椭圆长度", str(int(width))],
                ["椭圆高度", str(int(height))],
                ["填充颜色", f"{fill_color.red()},{fill_color.green()},{fill_color.blue()},{fill_color.alpha()}"],
                ["线条宽度", str(line_width)],
                ["线条颜色", f"{line_color.red()},{line_color.green()},{line_color.blue()},{line_color.alpha()}"],
                ["zValue",  str(zValue)]
            ] 

        elif isinstance(self.pointer, MyGraphicsLineItem):

            item: MyGraphicsLineItem = self.pointer
            width = item.pen().width()
            color = item.pen().color()
            length = round(item.line().length(),2)
            angle = round(item.line().angle(),2)
            zValue = item.zValue()

            self.data = [
                ["线宽", str(width)],
                ["颜色", f"{color.red()},{color.green()},{color.blue()},{color.alpha()}"],
                ["线长", str(length)],
                ["旋转角度", str(angle)],
                ["zValue",  str(zValue)]
            ]

        elif isinstance(self.pointer, MyGraphicsSimpleTextItem):
            item: MyGraphicsSimpleTextItem = self.pointer
            content = item.text()
            color = item.text_color_name
            font_size = item.font().pointSize()
            font_family = item.font().family()
            font_weight = item.font().weight()
            zValue = item.zValue()

            self.data = [
                ["内容", content],
                ["颜色", color],
                ["大小", str(font_size)],
                ["字体", font_family],
                ['字粗', font_weight],
                ['zValue', zValue]
            ]
        #print(self.data)
        # call this function to update the table view
        self.layoutChanged.emit()

    def update_source(self, row, col, value):
        if self.pointer is None:
            return
        if isinstance(self.pointer, MyPictureItem):
            item: MyPictureItem = self.pointer
            if self.table_structure["pic"][row] == "pic_location":
                try:
                    x, y = value.split(",")
                    item.setPos(int(x), int(y))
                except Exception as e:
                    traceback.print_exc()
                    pass
            elif self.table_structure["pic"][row] == "pic_width":
                try:
                    pix = QPixmap(item.pic_name_path).scaledToHeight(int(value),Qt.TransformationMode.SmoothTransformation)
                    item.picItem.setPixmap(pix)
                except Exception as e:
                    traceback.print_exc()
                    pass
            elif self.table_structure["pic"][row] == "text_location":
                try:
                    x, y = value.split(",")
                    item.textItem.setPos(int(x), int(y))
                except Exception as e:
                    traceback.print_exc()
                    pass
            elif self.table_structure["pic"][row] == "text_width":
                try:
                    txt: QGraphicsTextItem = item.textItem
                    txt.setTextWidth(int(value))
                except Exception as e:
                    traceback.print_exc()
                    pass
            elif self.table_structure["pic"][row] == "zValue":
                try:
                    item.setZValue(int(value))
                except Exception as e:
                    traceback.print_exc()
                    pass
            
            elif self.table_structure["pic"][row] == "device_sn":
                try:
                    item.device_sn = str(value)
                    item.textItem.setPlainText(MyPictureItem.get_chinese_name(item.pic_name))
                except Exception as e:
                    traceback.print_exc()
                    pass
                
        if isinstance(self.pointer, MyGraphicsRectItem):
            item: MyGraphicsRectItem = self.pointer
            if self.table_structure["rect"][row] == "rect_width":
                try:
                    item.setRect(item.rect().x(), item.rect().y(), int(value), item.rect().height())
                except Exception as e:
                    traceback.print_exc()
                    pass

            elif  self.table_structure["rect"][row] == "rect_height":
                try:
                    item.setRect(item.rect().x(), item.rect().y(), item.rect().width(), int(value))
                except Exception as e:
                    traceback.print_exc()
                    pass

            elif self.table_structure["rect"][row] == "fill_color":
                try:
                    r,g,b,a = value.split(",")
                    if not is_valid_color_value(r,g,b,a):
                        return
                    color = QColor(int(r),int(g),int(b),int(a))
                    #print(color)
                    item.setBrush(color)
                except Exception as e:
                    traceback.print_exc()
                    pass
            
            elif self.table_structure["rect"][row] == "line_width":
                try:
                    item.setPen(QPen(item.pen().color(), int(value)))
                except Exception as e:
                    traceback.print_exc()
                    pass
            
            elif self.table_structure["rect"][row] == "line_color":
                try:
                    r,g,b,a = value.split(",")
                    if not is_valid_color_value(r,g,b,a):
                        return
                    color = QColor(int(r),int(g),int(b),int(a))
                    item.setPen(QPen(color, item.pen().width()))
                except Exception as e:
                    traceback.print_exc()
                    pass
            
            elif self.table_structure["rect"][row] == "zValue":
                try:
                    item.setZValue(int(value))
                except Exception as e:
                    traceback.print_exc()
                    pass
        
        if isinstance(self.pointer, MyGraphicsEllipseItem):
            item: MyGraphicsEllipseItem = self.pointer
            if self.table_structure["ellipse"][row] == "ellipse_width":
                try:
                    item.setRect(item.rect().x(), item.rect().y(), int(value), item.rect().height())
                except Exception as e:
                    traceback.print_exc()
                    pass

            elif  self.table_structure["ellipse"][row] == "ellipse_height":
                try:
                    item.setRect(item.rect().x(), item.rect().y(), item.rect().width(), int(value))
                except Exception as e:
                    traceback.print_exc()
                    pass

            elif self.table_structure["ellipse"][row] == "fill_color":
                try:
                    r,g,b,a = value.split(",")
                    if not is_valid_color_value(r,g,b,a):
                        return
                    color = QColor(int(r),int(g),int(b),int(a))
                    item.setBrush(color)
                except Exception as e:
                    traceback.print_exc()
                    pass

            elif self.table_structure["ellipse"][row] == "line_width":
                try:
                    item.setPen(QPen(item.pen().color(), int(value)))
                except Exception as e:
                    traceback.print_exc()
                    pass

            elif self.table_structure["ellipse"][row] == "line_color":
                try:
                    r,g,b,a = value.split(",")
                    if not is_valid_color_value(r,g,b,a):
                        return
                    color = QColor(int(r),int(g),int(b),int(a))
                    item.setPen(QPen(color, item.pen().width()))
                except Exception as e:
                    traceback.print_exc()
                    pass

            elif self.table_structure["ellipse"][row] == "zValue":
                try:
                    item.setZValue(int(value))
                except Exception as e:
                    traceback.print_exc()
                    pass

        if isinstance(self.pointer, MyGraphicsLineItem):
            item: MyGraphicsLineItem = self.pointer
            if self.table_structure["line"][row] == "line_width":
                try:
                    item.setPen(QPen(item.pen().color(), int(value)))
                except Exception as e:
                    traceback.print_exc()
                    pass

            elif self.table_structure["line"][row] == "line_color":
                try:
                    r,g,b,a = value.split(",")
                    if not is_valid_color_value(r,g,b,a):
                        return
                    color = QColor(int(r),int(g),int(b),int(a))
                    item.setPen(QPen(color, item.pen().width()))
                except Exception as e:
                    traceback.print_exc()
                    pass

            elif self.table_structure["line"][row] == "line_length":
                try:
                    p1 = item.line().p1()
                    p2 = item.line().p2()
                    angle = item.line().angle()
                    length = float(value)
                    p2 = get_p2_from_p1(p1,length ,angle)
                    item.setLine(QLineF(p1, p2))
                
                except Exception as e:
                    traceback.print_exc()
                    pass

            elif self.table_structure["line"][row] == "rotate_angle":
                try:
                    p1 = item.line().p1()
                    p2 = item.line().p2()
                    length = item.line().length()
                    angle = float(value)
                    p2 = get_p2_from_p1(p1,length ,angle)
                    item.setLine(QLineF(p1, p2))
                except Exception as e:
                    traceback.print_exc()
                    pass

            elif self.table_structure["line"][row] == "zValue":
                try:
                    item.setZValue(int(value))
                except Exception as e:
                    traceback.print_exc()
                    pass

        if isinstance(self.pointer, MyGraphicsSimpleTextItem):
            
            item: MyGraphicsSimpleTextItem = self.pointer
            if self.table_structure["text"][row] == "text_content":
                try:
                    item.setText(value)
                except Exception as e:
                    traceback.print_exc()
                    pass
            elif self.table_structure["text"][row] == "text_color":
                try:
                    if not is_valid_color_name(value):
                        return
                    item.setBrush(QBrush(QColor(value)))
                    item.text_color_name = value
                except Exception as e:
                    traceback.print_exc()
                    pass

            elif self.table_structure["text"][row] == "text_size":
                try:
                    item.setFont(QFont(item.font().family(), int(value)))
                except Exception as e:
                    traceback.print_exc()
                    pass

            elif self.table_structure["text"][row] == "text_font":
                try:
                    font:QFont = item.font()
                    font.setFamily(str(value))
                    item.setFont(font)
                except Exception as e:
                    traceback.print_exc()
                    pass
            
            elif self.table_structure["text"][row] == "text_weight":
                try:
                    font:QFont = item.font()
                    font.setWeight(int(value))
                    item.setFont(font)
                except Exception as e:
                    traceback.print_exc()
                    pass

            elif self.table_structure["text"][row] == "zValue":
                try:
                    item.setZValue(int(value))
                except Exception as e:
                    traceback.print_exc()
                    pass

        
        ###############################################
        self.set_source(self.pointer)
        pass

    def clear_model(self):
        self.data = []
        self.layoutChanged.emit()
        pass

class MyGraphicView(QGraphicsView):
    def dragMoveEvent(self, e):
       pass
    
    def dragEnterEvent(self, e):

        if True:
            e.accept()
        else:
            e.ignore()
     
    def dropEvent(self, e:QDropEvent):
        picName = e.source().info['name']
        item = None
        
        if picName == "rectangle":
            item = MyGraphicsRectItem()
        elif picName == "ellipse":
            item = MyGraphicsEllipseItem()
        elif picName == "text":
            item = MyGraphicsSimpleTextItem()
        elif picName == "line":
            item = MyGraphicsLineItem()
        elif picName == "gas-meter":
            item = MyPictureItem("gas-meter")
        elif picName == "hydrant":
            item = MyPictureItem("hydrant")
        elif picName == "temp-meter":
            item = MyPictureItem("temp-meter")
        elif picName == "water-meter":
            item = MyPictureItem("water-meter")
        elif picName == "water-valve":
            item = MyPictureItem("water-valve")
        elif picName == "wind-meter":
            item = MyPictureItem("wind-meter")

        item.setPos(e.pos())
        self.scene().addItem(item)
        
        # 设置item可以移动
        #item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        # 设置item可以选中
        #item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        # 设置item可以聚焦，这样才会有键盘按键回调keyPressEvent
        #item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)

    def keyPressEvent(self, event:QKeyEvent):
        #print("123"+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        return super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = event.size()
        self.scene().setSceneRect(0, 0, size.width(), size.height())

    # 鼠标点击到item时，在属性表格中显示item的属性
    def mousePressEvent(self, event:QMouseEvent):
        #print("mousePressEvent" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if item:
                my_signal.set_table_properties_signal.emit(item)

        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event:QMouseEvent):
        #print("mouseReleaseEvent" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if item:
                my_signal.set_table_properties_signal.emit(item)
        return super().mouseReleaseEvent(event)
   
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("工控系统前端")
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        #self.current_grahics_item = None
        #print(id(self))
        # main layout
        self.main_layout =  QHBoxLayout(central_widget)
        self.is_watch_mode = False

        self.init_left()
        self.init_center_and_right()
        self.init_toolbar()

        th = threading.Thread(target=self.thread_network)
        th.setDaemon(True)
        th.start()

        my_signal.set_table_properties_signal.connect(self.table_model.set_source)
        my_signal.clear_table_properties_signal.connect(self.table_model.clear_model)
        my_signal.update_mypicture_signal.connect(self.update_mypicture)
        
        self.open_action.triggered.connect(self.open_file_operate)
        self.save_action.triggered.connect(self.save_file_operate)
        self.delete_action.triggered.connect(self.delete_item_operate)
        self.clear_action.triggered.connect(self.clear_operate)
        self.edit_action.triggered.connect(self.edit_mode_operate)
        self.watch_action.triggered.connect(self.watch_mode_operate)

        self.installEventFilter(self)

        pass

    def init_left(self):             
            
        self.left_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_layout)

        self.grid_layout = QGridLayout()
        self.left_layout.addLayout(self.grid_layout)
        self.left_layout.addStretch()
        

        for i in range(len(image_list)):
            for j in range(len(image_list[i])):
                label = DragLabel()
                label.setPixmap(QPixmap(f"./images/{image_list[i][j]}.png"))
                label.info = {"name":image_list[i][j]}
                self.grid_layout.addWidget(label,i,j)

    def init_center_and_right(self):
        self.scene = QGraphicsScene(0,0,800,600)
        self.view = MyGraphicView(self.scene)

        self.table_model = MyTableModel()
        self.property_table = QTableView()
        self.property_table.setModel(self.table_model)
        self.property_table.verticalHeader().setVisible(False)
        self.property_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        #self.property_table.cellChanged.connect(self.update_item_property)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        #设定splitter可拖动
        splitter.addWidget(self.view)

        splitter.addWidget(self.property_table)
        self.main_layout.addWidget(splitter)
        #设置splitter禁止塌陷
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

    def init_toolbar(self):
        self.toolbar = self.addToolBar("工具栏")
        self.toolbar.setStyleSheet("QToolBar{spacing:10px;padding:2px;}")
        self.open_action = QAction(QIcon(open_icon_path),"打开", self)
        self.save_action = QAction(QIcon(save_icon_path),"保存", self)
        self.delete_action = QAction(QIcon(delete_icon_path),"删除", self)
        self.clear_action = QAction(QIcon(clear_icon_path),"清空", self)
        self.edit_action = QAction(QIcon(edit_icon_path),"编辑", self)
        self.watch_action = QAction(QIcon(watch_icon_path),"查看", self)
        self.toolbar.setContentsMargins(20,0,0,0)
        self.toolbar.addAction(self.open_action)
        self.toolbar.addAction(self.save_action)
        self.toolbar.addAction(self.delete_action)
        self.toolbar.addAction(self.clear_action)
        self.toolbar.addAction(self.edit_action)
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)
        pass

    def thread_network(self):        

        self.client_socket = None
        self.is_connected = False

        while True:
            # 连接服务器，要求支持服务器断开后持续重连

            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((server_address, server_port))
            except:
                print("连接失败，正在重试...")
                self.client_socket = None
                self.is_connected = False
                time.sleep(1)
                continue

            self.is_connected = True
            while True:
                try:
                    response = self.client_socket.recv(1024)
                    #print(response)
                    res:str = response.decode("ANSI")
                    dict_obj = self.extract_network_response(res)
                    if dict_obj is not None:
                        my_signal.update_mypicture_signal.emit(json.dumps(dict_obj))
                        pass
                except socket.error as e:
                    print(e)
                    self.client_socket.close()
                    self.client_socket = None
                    self.is_connected = False
                    break

    def open_file_operate(self):
        open_file = QFileDialog.getOpenFileName(self,"打开设计文件", "./",filter_str)
        if open_file[0] is not None and open_file[0] != "" and open_file[0].endswith(suffix):
            print(open_file[0])
            self.scene.clear()
            with open(open_file[0], "r", encoding="utf-8") as f:
                data = json.load(f)
                for item_dict in data:
                    if item_dict["type"] == "MyPictureItem":
                        item : MyPictureItem = MyPictureItem(
                            pic_name = item_dict["pic_name"],
                            #text = item_dict["text"],
                            #pos = QPointF(float(item_dict["pos"][0]), float(item_dict["pos"][1])),
                            icon_width = item_dict["icon_width"],
                            #text_relevate_pos = QPointF(float(item_dict["text_relative"][0]), float(item_dict["text_relative"][1])),
                            #text_width = item_dict["text_width"],
                            zValue = item_dict["zValue"],

                        )

                        #还不能写在构造中
                        item.setPos(float(item_dict["pos"][0]), float(item_dict["pos"][1]))
                        item.device_sn = item_dict.get('device_sn',None)
                        self.scene.addItem(item)
                    
                    elif item_dict["type"] == "MyGraphicsRectItem":
                        item : MyGraphicsRectItem = MyGraphicsRectItem(
                            pos = QPointF(float(item_dict["pos"][0]), float(item_dict["pos"][1])),
                            rectSize = QRectF(float(item_dict["rect"][0]), float(item_dict["rect"][1]),
                                               float(item_dict["rect"][2]), float(item_dict["rect"][3])),
                            rectPen = QPen(QColor(item_dict["pen_color"][0],item_dict["pen_color"][1],item_dict["pen_color"][2],item_dict["pen_color"][3]), item_dict["pen_width"]),
                            rectBrush = QBrush(QColor(item_dict["brush_color"][0],item_dict["brush_color"][1],item_dict["brush_color"][2],item_dict["brush_color"][3])),
                            zValue = item_dict["zValue"]
                        )
                        self.scene.addItem(item)
                    
                    elif item_dict["type"] == "MyGraphicsLineItem":
                        item : MyGraphicsLineItem = MyGraphicsLineItem(
                            pos = QPointF(float(item_dict["pos"][0]), float(item_dict["pos"][1])),
                            start = QPointF(float(item_dict["start"][0]), float(item_dict["start"][1])),
                            pen = QPen(QColor(item_dict["pen_color"][0], item_dict["pen_color"][1], item_dict["pen_color"][2], item_dict["pen_color"][3]), item_dict["pen_width"]),
                            length = item_dict["length"],
                            angle = item_dict["angle"],
                            zValue = item_dict["zValue"]
                        )
                        self.scene.addItem(item)

                    elif item_dict["type"] == "MyGraphicsEllipseItem":
                        item : MyGraphicsEllipseItem = MyGraphicsEllipseItem(
                            pos = QPointF(float(item_dict["pos"][0]), float(item_dict["pos"][1])),
                            rect = QRectF(float(item_dict["rect"][0]), float(item_dict["rect"][1]), float(item_dict["rect"][2]), float(item_dict["rect"][3])),
                            pen = QPen(QColor(item_dict["pen_color"][0], item_dict["pen_color"][1], item_dict["pen_color"][2], item_dict["pen_color"][3]), item_dict["pen_width"]),
                            brush = QBrush(QColor(item_dict["brush_color"][0], item_dict["brush_color"][1], item_dict["brush_color"][2], item_dict["brush_color"][3]))
                            )
                        self.scene.addItem(item)

                    elif item_dict["type"] == "MyGraphicsSimpleTextItem":
                        item : MyGraphicsSimpleTextItem = MyGraphicsSimpleTextItem(
                            pos = QPointF(float(item_dict["pos"][0]), float(item_dict["pos"][1])),
                            word = item_dict["text"],
                            input_text_color = item_dict["text_color"], 
                            font = QFont(item_dict["font_family"], item_dict["font_size"], item_dict["font_weight"]),
                            zValue = item_dict["zValue"]
                        )
                        self.scene.addItem(item)
                        pass

        if self.is_watch_mode == True:      
            self.set_all_item_in_scene_readonly(True)
        pass

    def save_file_operate(self):
        save_file = QFileDialog.getSaveFileName(self,"保存设计文件", "./",filter_str)
        print(save_file[0])
        if save_file[0] is not None and save_file[0] != "":
            items = self.scene.items()
            result = []
            for (index, item) in enumerate(items):
                if isinstance(item, MyPictureItem) or isinstance(item, MyGraphicsRectItem) or isinstance(item, MyGraphicsLineItem) or isinstance(item, MyGraphicsEllipseItem) or isinstance(item, MyGraphicsSimpleTextItem):
                    item_str = (item.to_dict())
                    result.append(item_str)

            with open(save_file[0], "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
        pass

    def delete_item_operate(self):
        if self.table_model.pointer is not None and self.table_model.pointer in self.scene.items():
            print(self)
            self.scene.removeItem(self.table_model.pointer)
            my_signal.clear_table_properties_signal.emit()
        pass

    def clear_operate(self):
        self.scene.clear()

    def edit_mode_operate(self):
        #进入查看模式True 
        self.is_watch_mode = True

        self.toolbar.removeAction(self.edit_action)
        self.toolbar.addAction(self.watch_action)
        self.delete_action.setEnabled(False)
        self.clear_action.setEnabled(False)

        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            if item is not None:
                item.widget().setEnabled(False)

        self.grid_layout.setEnabled(False)
        # 允许所有item的移动和聚焦
        self.set_all_item_in_scene_readonly(True)
        pass

    def watch_mode_operate(self):
        self.is_watch_mode = False

        self.toolbar.removeAction(self.watch_action)
        self.toolbar.addAction(self.edit_action)

        self.delete_action.setEnabled(True)
        self.clear_action.setEnabled(True)

        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            if item is not None:
                item.widget().setEnabled(True)

        # 禁止所有item的移动和聚焦
        self.set_all_item_in_scene_readonly(False)
        pass

    def eventFilter(self, watched, event:QEvent):
        if event.type() == QEvent.Type.KeyPress:
            
            if self.table_model.pointer not in self.scene.items():
                my_signal.clear_table_properties_signal.emit()   #清空属性表格

        return super().eventFilter(watched, event)

    def extract_network_response(self, strings: str) -> dict:
        #BF01|notify-to-frontend|0|1739954257839825${"device-sn":"aaaa0002","humidity":"49.510","temperature":"25.040"}\x04
        if "BF" not in strings or "notify-to-frontend" not in strings:
            return None
        head = strings.find("$")
        tail = strings.find("\04")
        if head < 0 or tail < 0:
            return None
        try:
            obj = json.loads(strings[head + 1 : tail])
        except :
            print("解析失败")
            return None
        return obj

    def update_mypicture(self, data:str):
        obj:dict = json.loads(data)
        if obj is None:
            return
        device_sn = obj.get("device-sn",None)
        CO = obj.get("CO",None)
        HCL = obj.get("HCL",None)
        SO2 = obj.get("SO2",None)
        humidity = obj.get("humidity",None)
        temperature = obj.get("temperature",None)
        water_pressure = obj.get("water-pressure",None)
        flow_rate = obj.get("flow-rate",None)
        device_type = None
        msg = None

        if CO is not None :
            device_type = "gas-meter"
            msg = f"CO:{CO}\n"
            if HCL is not None:
                msg += f"HCL:{HCL}\n"
            if SO2 is not None:
                msg += f"SO2:{SO2}\n"
            msg = msg[:-1]

        elif temperature is not None:
            device_type = "temp-meter"
            msg = f"温度:{temperature}\n"
            if humidity is not None:
                msg += f"湿度:{humidity}\n"
            msg = msg[:-1]

        elif water_pressure is not None:
            device_type = "water-meter"
            msg = f"水压:{water_pressure}\n"
            if flow_rate is not None:
                msg += f"流速:{flow_rate}\n"
            msg = msg[:-1]

        elif flow_rate is not None:
            device_type = "wind-meter"
            msg = f"风速:{flow_rate}\n"
        else:
            device_type = "unknown"
            #print("未知设备")
            return
        
        msg_is_processed = False
        for item in self.scene.items():
            if isinstance(item, MyPictureItem):
                if item.device_sn == device_sn and item.pic_name == device_type:
                    item:MyPictureItem
                    item.textItem.setPlainText(msg)
                    item.textItem.setPos(QPoint(0,40))
                    item.textItem.setTextWidth(100)
                    msg_is_processed = True
        
        if not msg_is_processed:
            #print("未处理的设备消息")
            pass
        pass

    def set_all_item_in_scene_readonly(self, readonly:bool):
        for item in self.scene.items():
            if isinstance(item, MyPictureItem) or isinstance(item, MyGraphicsRectItem) or isinstance(item, MyGraphicsLineItem) or isinstance(item, MyGraphicsEllipseItem) or isinstance(item, MyGraphicsSimpleTextItem):

                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not readonly)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, not readonly)
                #if isinstance(item, MyGraphicsRectItem) or isinstance(item, MyGraphicsLineItem) or isinstance#(item, MyGraphicsEllipseItem):
                    #item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, not readonly)


'''
    def add_item_to_scene(self, item):
        self.scene.addItem(item)

        # 设置item可以移动
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        # 设置item可以选中
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        # 设置item可以聚焦，这样才会有键盘按键回调keyPressEvent
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
'''
'''
    def set_table_properties(self, item):
        self.property_table.current_graphics_item = item
        if isinstance(item, MyGraphicsPixmapItem):
            print("MyGraphicsPixmapItem")
            
        elif isinstance(item, MyGraphicsRectItem):
            #print("MyGraphicsRectItem")
            item : MyGraphicsRectItem
            self.property_table.setRowCount(0)

            table_rect = table_data["rect"]
            rect = item.rect()
            for i in range(len(table_rect)):
                self.property_table.insertRow(i)
                widget_item = QTableWidgetItem(table_rect[i][2])
                widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.property_table.setItem(i,0,widget_item)
            
                if table_rect[i][1] == "rect_width":
                    widget_item = QTableWidgetItem(str(int(rect.width())))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)
                
                elif table_rect[i][1] == "rect_height":
                    widget_item = QTableWidgetItem(str(int(rect.height())))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_rect[i][1] == "fill_color":
                    brush = item.brush()
                    color = brush.color()
                    color_str = f"{color.red()},{color.green()},{color.blue()},{color.alpha()}"
                    widget_item = QTableWidgetItem(color_str)
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_rect[i][1] == "line_width":
                    width = item.pen().width()
                    widget_item = QTableWidgetItem(str(width))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_rect[i][1] == "line_color":
                    color = item.pen().color()
                    color_str = f"{color.red()},{color.green()},{color.blue()},{color.alpha()}"
                    widget_item = QTableWidgetItem(color_str)
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_rect[i][1] == "zValue":
                    zValue = item.zValue()
                    widget_item = QTableWidgetItem(str(zValue))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

        elif isinstance(item, MyGraphicsLineItem):
            #print("MyGraphicsLineItem")
            item: MyGraphicsLineItem
            self.property_table.setRowCount(0)

            table_line = table_data["line"]
            for i in range(len(table_line)):
                self.property_table.insertRow(i)
                widget_item = QTableWidgetItem(table_line[i][2])
                widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.property_table.setItem(i,0,widget_item)

                if table_line[i][1] == "line_width":
                    width = item.pen().width()
                    widget_item = QTableWidgetItem(str(width))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)
                
                elif table_line[i][1] == "line_color":
                    color = item.pen().color()
                    color_str = f"{color.red()},{color.green()},{color.blue()},{color.alpha()}"
                    widget_item = QTableWidgetItem(color_str)
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_line[i][1] == "line_length":
                    length = item.line().length()
                    widget_item = QTableWidgetItem(str(round(length,2)))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_line[i][1] == "rotate_angle":
                    angle = item.line().angle()
                    widget_item = QTableWidgetItem(str(round(angle,2)))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_line[i][1] == "zValue":
                    zValue = item.zValue()
                    widget_item = QTableWidgetItem(str(zValue))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

        #elif isinstance(item, MyGraphicsSimpleTextItem):
        #    print("MyGraphicsSimpleTextItem")
        elif isinstance(item, MyGraphicsEllipseItem):
            item: MyGraphicsEllipseItem
            self.property_table.setRowCount(0)

            table_ellipse = table_data["ellipse"]
            rect = item.rect()
            for i in range(len(table_ellipse)):
                self.property_table.insertRow(i)
                widget_item = QTableWidgetItem(table_ellipse[i][2])
                widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.property_table.setItem(i,0,widget_item)

                if table_ellipse[i][1] == "ellipse_width":
                    widget_item = QTableWidgetItem(str(int(rect.width())))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)
                
                elif table_ellipse[i][1] == "ellipse_height":
                    widget_item = QTableWidgetItem(str(int(rect.height())))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_ellipse[i][1] == "fill_color":
                    color = item.brush().color()
                    color_str = f"{color.red()},{color.green()},{color.blue()},{color.alpha()}"
                    widget_item = QTableWidgetItem(color_str)
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_ellipse[i][1] == "line_width":
                    width = item.pen().width()
                    widget_item = QTableWidgetItem(str(width))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_ellipse[i][1] == "line_color":
                    color = item.pen().color()
                    color_str = f"{color.red()},{color.green()},{color.blue()},{color.alpha()}"
                    widget_item = QTableWidgetItem(color_str)
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_ellipse[i][1] == "zValue":
                    zValue = item.zValue()
                    widget_item = QTableWidgetItem(str(zValue))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

        elif isinstance(item, MyPictureItem):

            item : MyGraphicsRectItem
            self.property_table.setRowCount(0)

            table_pic = table_data["pic"]
            for i in range(len(table_pic)):
                self.property_table.insertRow(i)
                widget_item = QTableWidgetItem(table_pic[i][2])
                widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.property_table.setItem(i,0,widget_item)

                if table_pic[i][1] == "pic_location":
                    widget_item = QTableWidgetItem(str(int(item.x())) + \
                                                             "," + str(int(item.y())))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_pic[i][1] == "pic_width":
                    rect = item.boundingRect()   
                    widget_item = QTableWidgetItem(str(int(rect.width())))     
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)
                
                elif table_pic[i][1] == "text_location":
                    widget_item = QTableWidgetItem(str(int(item.textItem.x())) + \
                                                             "," + str(int(item.textItem.y())))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_pic[i][1] == "text_width":
                    widget_item = QTableWidgetItem(str(int(item.textItem.font().pointSize())))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_pic[i][1] == "zValue":
                    widget_item = QTableWidgetItem(str(item.zValue()))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

        elif isinstance(item, MyGraphicsSimpleTextItem):
            item: MyGraphicsSimpleTextItem
            self.property_table.setRowCount(0)

            table_text = table_data["text"]

            for i in range(len(table_text)):
                self.property_table.insertRow(i)
                widget_item = QTableWidgetItem(table_text[i][2])
                widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.property_table.setItem(i,0,widget_item)

                if table_text[i][1] == "text_content":
                    widget_item = QTableWidgetItem(item.text())
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)
                
                elif table_text[i][1] == "text_color":
                    widget_item = QTableWidgetItem(item.text_color_name)
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)
                
                elif table_text[i][1] == "text_size":
                    widget_item = QTableWidgetItem(str(item.font().pointSize()))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_text[i][1] == "text_font":
                    widget_item = QTableWidgetItem(item.font().family())
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_text[i][1] == "text_weight":
                    widget_item = QTableWidgetItem(str(item.font().weight()))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.property_table.setItem(i,1,widget_item)

                elif table_text[i][1] == "zValue":
                    widget_item = QTableWidgetItem(str(item.zValue()))
                    widget_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  
                    self.property_table.setItem(i,1,widget_item)

        elif item is None:
            self.property_table.setRowCount(0)


        pass
    
    def update_item(self, property_type, value):
        current_item = self.property_table.current_graphics_item
        print("update table")
        if current_item is None:
            return
        if isinstance(current_item, MyPictureItem):
            current_item: MyPictureItem
            if property_type == "pic_location":
                x, y = value.split(",")
                current_item.setPos(int(x), int(y))
            elif property_type == "pic_width":
                pass
'''

if __name__ == '__main__':
    app = QApplication([])
    app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.Round)
    window = MainWindow()
    window.show()
    app.exec_()
