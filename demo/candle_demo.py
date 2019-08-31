# -*- coding: utf-8 -*-
'''
@author : 景色
@csdn : https://blog.csdn.net/pjjing
@QQ群 : 767101469
@公众号 : QuantRoad2019
'''
import thostmduserapi as mdapi
from datetime import time
from typing import List, Dict, Type,Tuple
from PyQt5 import QtGui, QtWidgets, QtCore
from abc import abstractmethod
import pyqtgraph as pg


WHITE_COLOR = (255, 255, 255)
BLACK_COLOR = (0, 0, 0)
GREY_COLOR = (100, 100, 100)

UP_COLOR = (255, 0, 0)
DOWN_COLOR = (0, 255, 50)
CURSOR_COLOR = (255, 245, 162)

PEN_WIDTH = 1
BAR_WIDTH = 0.4

AXIS_WIDTH = 0.8
NORMAL_FONT = QtGui.QFont("Arial", 9)


class CBarData:
    def _init__(self):
        self.instrumentID: str
        self.updateTime: time
        self.volume: float = 0
        self.openInterest: float = 0
        self.openPrice: float = 0
        self.highPrice: float = 0
        self.lowPrice: float = 0
        self.closePrice: float = 0

class BarManager:
    """"""

    def __init__(self):
        """"""
        self._bars: Dict[time, CBarData] = {}
        self._datetime_index_map: Dict[time, int] = {}
        self._index_datetime_map: Dict[int, time] = {}

        self._price_ranges: Dict[Tuple[int, int], Tuple[float, float]] = {}
        self._volume_ranges: Dict[Tuple[int, int], Tuple[float, float]] = {}
    
    def update_bar(self, bar: CBarData) -> None:
        """
        Update one single bar data.
        """
        dt = bar.updateTime
        if dt not in self._datetime_index_map:
            ix = len(self._bars)
            self._datetime_index_map[dt] = ix
            self._index_datetime_map[ix] = dt

        self._bars[dt] = bar
        self._clear_cache()

    def get_count(self) -> int:
        """
        Get total number of bars.
        """
        return len(self._bars)

    def get_index(self, dt: time) -> int:
        """
        Get index with datetime.
        """
        return self._datetime_index_map.get(dt, None)

    def get_datetime(self, ix: float) -> time:
        """
        Get datetime with index.
        """
        ix = to_int(ix)
        return self._index_datetime_map.get(ix, None)

    def get_bar(self, ix: float) -> CBarData:
        """
        Get bar data with index.
        """
        ix = to_int(ix)
        dt = self._index_datetime_map.get(ix, None)
        if not dt:
            return None

        return self._bars[dt]

    def get_all_bars(self) -> List[CBarData]:
        """
        Get all bar data.
        """
        return list(self._bars.values())

    def get_price_range(self, min_ix: float = None, max_ix: float = None) -> Tuple[float, float]:
        """
        Get price range to show within given index range.
        """
        if not self._bars:
            return 0, 1

        if not min_ix:
            min_ix = 0
            max_ix = len(self._bars) - 1
        else:
            min_ix = to_int(min_ix)
            max_ix = to_int(max_ix)
            max_ix = min(max_ix, self.get_count())

        buf = self._price_ranges.get((min_ix, max_ix), None)
        if buf:
            return buf

        bar_list = list(self._bars.values())[min_ix:max_ix + 1]
        first_bar = bar_list[0]
        max_price = first_bar.highPrice
        min_price = first_bar.lowPrice

        for bar in bar_list[1:]:
            max_price = max(max_price, bar.highPrice)
            min_price = min(min_price, bar.lowPrice)

        self._price_ranges[(min_ix, max_ix)] = (min_price, max_price)
        return min_price, max_price

    def get_volume_range(self, min_ix: float = None, max_ix: float = None) -> Tuple[float, float]:
        """
        Get volume range to show within given index range.
        """
        if not self._bars:
            return 0, 1

        if not min_ix:
            min_ix = 0
            max_ix = len(self._bars) - 1
        else:
            min_ix = to_int(min_ix)
            max_ix = to_int(max_ix)
            max_ix = min(max_ix, self.get_count())

        buf = self._volume_ranges.get((min_ix, max_ix), None)
        if buf:
            return buf

        bar_list = list(self._bars.values())[min_ix:max_ix + 1]

        first_bar = bar_list[0]
        max_volume = first_bar.volume
        min_volume = 0

        for bar in bar_list[1:]:
            max_volume = max(max_volume, bar.volume)

        self._volume_ranges[(min_ix, max_ix)] = (min_volume, max_volume)
        return min_volume, max_volume

    def _clear_cache(self) -> None:
        """
        Clear cached range data.
        """
        self._price_ranges.clear()
        self._volume_ranges.clear()

    def clear_all(self) -> None:
        """
        Clear all data in manager.
        """
        self._bars.clear()
        self._datetime_index_map.clear()
        self._index_datetime_map.clear()

        self._clear_cache()

def to_int(value: float) -> int:
    """"""
    return int(round(value, 0))

class DatetimeAxis(pg.AxisItem):
    """"""

    def __init__(self, manager: BarManager, *args, **kwargs):
        """"""
        super().__init__(*args, **kwargs)

        self._manager: BarManager = manager

        self.setPen(width=AXIS_WIDTH)
        self.tickFont = NORMAL_FONT

    def tickStrings(self, values: List[int], scale: float, spacing: int):
        """
        Convert original index to datetime string.
        """
        strings = []

        for ix in values:
            dt = self._manager.get_datetime(ix)
            
            if not dt:
                s = ""
            elif dt.hour:
                s = dt.strftime("%H:%M:%S")
            else:
                s = dt.strftime("%Y-%m-%d")

            strings.append(s)

        return strings


class ChartItem(pg.GraphicsObject):
    """"""

    def __init__(self, manager: BarManager):
        """"""
        super().__init__()

        self._manager: BarManager = manager

        self._bar_picutures: Dict[int, QtGui.QPicture] = {}
        self._item_picuture: QtGui.QPicture = None

        self._up_pen: QtGui.QPen = pg.mkPen(
            color=UP_COLOR, width=PEN_WIDTH
        )
        self._up_brush: QtGui.QBrush = pg.mkBrush(color=UP_COLOR)

        self._down_pen: QtGui.QPen = pg.mkPen(
            color=DOWN_COLOR, width=PEN_WIDTH
        )
        self._down_brush: QtGui.QBrush = pg.mkBrush(color=DOWN_COLOR)

        self._rect_area: Tuple[float, float] = None

        # Very important! Only redraw the visible part and improve speed a lot.
        self.setFlag(self.ItemUsesExtendedStyleOption)

    @abstractmethod
    def _draw_bar_picture(self, ix: int, bar: CBarData) -> QtGui.QPicture:
        """
        Draw picture for specific bar.
        """
        pass

    @abstractmethod
    def boundingRect(self) -> QtCore.QRectF:
        """
        Get bounding rectangles for item.
        """
        pass

    @abstractmethod
    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """
        Get range of y-axis with given x-axis range.

        If min_ix and max_ix not specified, then return range with whole data set.
        """
        pass

    @abstractmethod
    def get_info_text(self, ix: int) -> str:
        """
        Get information text to show by cursor.
        """
        pass

    def update_history(self, history: List[CBarData]) -> CBarData:
        """
        Update a list of bar data.
        """
        self._bar_picutures.clear()

        bars = self._manager.get_all_bars()
        for ix, bar in enumerate(bars):
            bar_picture = self._draw_bar_picture(ix, bar)
            self._bar_picutures[ix] = bar_picture

        self.update()

    def update_bar(self, bar: CBarData) -> CBarData:
        """
        Update single bar data.
        """
        ix = self._manager.get_index(bar.updateTime)
        bar_picture = self._draw_bar_picture(ix, bar)
        self._bar_picutures[ix] = bar_picture
        self.update()

    def update(self) -> None:
        """
        Refresh the item.
        """
        if self.scene():
           self.scene().update()

    def paint(
        self,
        painter: QtGui.QPainter,
        opt: QtWidgets.QStyleOptionGraphicsItem,
        w: QtWidgets.QWidget
    ):
        """
        Reimplement the paint method of parent class.

        This function is called by external QGraphicsView.
        """
        rect = opt.exposedRect

        min_ix = int(rect.left())
        max_ix = int(rect.right())
        max_ix = min(max_ix, len(self._bar_picutures))

        rect_area = (min_ix, max_ix)
        if rect_area != self._rect_area or not self._item_picuture:
            self._rect_area = rect_area
            self._draw_item_picture(min_ix, max_ix)

        self._item_picuture.play(painter)

    def _draw_item_picture(self, min_ix: int, max_ix: int) -> None:
        """
        Draw the picture of item in specific range.
        """
        self._item_picuture = QtGui.QPicture()
        painter = QtGui.QPainter(self._item_picuture)

        for n in range(min_ix, max_ix):
            bar_picture = self._bar_picutures[n]
            bar_picture.play(painter)

        painter.end()

    def clear_all(self) -> None:
        """
        Clear all data in the item.
        """
        self._item_picuture = None
        self._bar_picutures.clear()
        self.update()

class CandleItem(ChartItem):
    """"""

    def __init__(self, manager: BarManager):
        """"""
        super().__init__(manager)

    def _draw_bar_picture(self, ix: int, bar: CBarData) -> QtGui.QPicture:
        """"""
        # Create objects
        candle_picture = QtGui.QPicture()
        painter = QtGui.QPainter(candle_picture)

        # Set painter color
        if bar.closePrice >= bar.openPrice:
            painter.setPen(self._up_pen)
            painter.setBrush(self._up_brush)
        else:
            painter.setPen(self._down_pen)
            painter.setBrush(self._down_brush)
            
        painter.drawLine(QtCore.QPointF(ix, bar.lowPrice), QtCore.QPointF(ix, bar.highPrice))
        painter.drawRect(QtCore.QRectF(
                ix - BAR_WIDTH,
                bar.openPrice,
                BAR_WIDTH * 2,
                bar.closePrice - bar.openPrice
            ))        
        
        # Finish
        painter.end()
        return candle_picture

    def boundingRect(self) -> QtCore.QRectF:
        """"""
        min_price, max_price = self._manager.get_price_range()
        rect = QtCore.QRectF(
            0,
            min_price,
            len(self._bar_picutures),
            max_price - min_price
        )
        return rect

    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """
        Get range of y-axis with given x-axis range.

        If min_ix and max_ix not specified, then return range with whole data set.
        """
        min_price, max_price = self._manager.get_price_range(min_ix, max_ix)
        return min_price, max_price

    def get_info_text(self, ix: int) -> str:
        """
        Get information text to show by cursor.
        """
        bar = self._manager.get_bar(ix)

        if bar:
            words = [
                "Time",
                bar.updateTime.strftime("%H:%M"),
                "",
                "Open",
                str(bar.openPrice),
                "",
                "High",
                str(bar.highPrice),
                "",
                "Low",
                str(bar.lowPrice),
                "",
                "Close",
                str(bar.closePrice)
            ]
            text = "\n".join(words)
        else:
            text = ""

        return text


class ChartWidget(pg.PlotWidget):
    """"""
    MIN_BAR_COUNT = 60

    def __init__(self, parent: QtWidgets.QWidget = None):
        """"""
        super().__init__(parent)

        self._manager: BarManager = BarManager()

        self._plots: Dict[str, pg.PlotItem] = {}
        self._items: Dict[str, ChartItem] = {}
        self._item_plot_map: Dict[ChartItem, pg.PlotItem] = {}

        self._first_plot: pg.PlotItem = None
        self._cursor: ChartCursor = None

        self._right_ix: int = 0                     # Index of most right data
        self._bar_count: int = self.MIN_BAR_COUNT   # Total bar visible in chart

        self._init_ui()

    def _init_ui(self) -> None:
        """"""
        self.setWindowTitle("程序化交易入门(QuantRoad2019)")

        self._layout = pg.GraphicsLayout()
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(0)
        self._layout.setBorder(color=GREY_COLOR, width=0.8)
        self._layout.setZValue(0)
        self.setCentralItem(self._layout)

        self._x_axis = DatetimeAxis(self._manager, orientation='bottom')

    def add_cursor(self) -> None:
        """"""
        if not self._cursor:
            self._cursor = ChartCursor(
                self, self._manager, self._plots, self._item_plot_map)

    def add_plot(
        self,
        plot_name: str,
        minimum_height: int = 80,
        maximum_height: int = None,
        hide_x_axis: bool = False
    ) -> None:
        """
        Add plot area.
        """
        # Create plot object
        plot = pg.PlotItem(axisItems={'bottom': self._x_axis})
        plot.setMenuEnabled(False)
        plot.setClipToView(True)
        plot.hideAxis('left')
        plot.showAxis('right')
        plot.setDownsampling(mode='peak')
        plot.setRange(xRange=(0, 1), yRange=(0, 1))
        plot.hideButtons()
        plot.setMinimumHeight(minimum_height)

        if maximum_height:
            plot.setMaximumHeight(maximum_height)

        if hide_x_axis:
            plot.hideAxis("bottom")

        if not self._first_plot:
            self._first_plot = plot

        # Connect view change signal to update y range function
        view = plot.getViewBox()
        view.sigXRangeChanged.connect(self._update_y_range)
        view.setMouseEnabled(x=True, y=False)

        # Set right axis
        right_axis = plot.getAxis('right')
        right_axis.setWidth(60)
        right_axis.tickFont = NORMAL_FONT

        # Connect x-axis link
        if self._plots:
            first_plot = list(self._plots.values())[0]
            plot.setXLink(first_plot)

        # Store plot object in dict
        self._plots[plot_name] = plot

    def add_item(
        self,
        item_class: Type[ChartItem],
        item_name: str,
        plot_name: str
    ):
        """
        Add chart item.
        """
        item = item_class(self._manager)
        self._items[item_name] = item

        plot = self._plots.get(plot_name)
        plot.addItem(item)
        self._item_plot_map[item] = plot

        self._layout.nextRow()
        self._layout.addItem(plot)

    def get_plot(self, plot_name: str) -> pg.PlotItem:
        """
        Get specific plot with its name.
        """
        return self._plots.get(plot_name, None)

    def get_all_plots(self) -> List[pg.PlotItem]:
        """
        Get all plot objects.
        """
        return self._plots.values()

    def clear_all(self) -> None:
        """
        Clear all data.
        """
        self._manager.clear_all()

        for item in self._items.values():
            item.clear_all()

        if self._cursor:
            self._cursor.clear_all()

    def update_history(self, history: List[CBarData]) -> None:
        """
        Update a list of bar data.
        """
        self._manager.update_history(history)

        for item in self._items.values():
            item.update_history(history)

        self._update_plot_limits()

        self.move_to_right()

    def update_bar(self, bar: CBarData) -> None:
        """
        Update single bar data.
        """
        self._manager.update_bar(bar)
        for item in self._items.values():
            item.update_bar(bar)
        self._update_plot_limits()
        if self._right_ix >= (self._manager.get_count() - self._bar_count / 2):
            self.move_to_right()

    def _update_plot_limits(self) -> None:
        """
        Update the limit of plots.
        """
        for item, plot in self._item_plot_map.items():
            min_value, max_value = item.get_y_range()

            plot.setLimits(
                xMin=-1,
                xMax=self._manager.get_count(),
                yMin=min_value,
                yMax=max_value
            )

    def _update_x_range(self) -> None:
        """
        Update the x-axis range of plots.
        """
        max_ix = self._right_ix
        min_ix = self._right_ix - self._bar_count

        for plot in self._plots.values():
            plot.setRange(xRange=(min_ix, max_ix), padding=0)

    def _update_y_range(self) -> None:
        """
        Update the y-axis range of plots.
        """
        view = self._first_plot.getViewBox()
        view_range = view.viewRange()

        min_ix = max(0, int(view_range[0][0]))
        max_ix = min(self._manager.get_count(), int(view_range[0][1]))

        # Update limit for y-axis
        for item, plot in self._item_plot_map.items():
            y_range = item.get_y_range(min_ix, max_ix)
            plot.setRange(yRange=y_range)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """
        Reimplement this method of parent to update current max_ix value.
        """
        view = self._first_plot.getViewBox()
        view_range = view.viewRange()
        self._right_ix = max(0, view_range[0][1])

        super().paintEvent(event)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """
        Reimplement this method of parent to move chart horizontally and zoom in/out.
        """
        if event.key() == QtCore.Qt.Key_Left:
            self._on_key_left()
        elif event.key() == QtCore.Qt.Key_Right:
            self._on_key_right()
        elif event.key() == QtCore.Qt.Key_Up:
            self._on_key_up()
        elif event.key() == QtCore.Qt.Key_Down:
            self._on_key_down()

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """
        Reimplement this method of parent to zoom in/out.
        """
        delta = event.angleDelta()

        if delta.y() > 0:
            self._on_key_up()
        elif delta.y() < 0:
            self._on_key_down()

    def _on_key_left(self) -> None:
        """
        Move chart to left.
        """
        self._right_ix -= 1
        self._right_ix = max(self._right_ix, self._bar_count)

        self._update_x_range()
        self._cursor.move_left()
        self._cursor.update_info()

    def _on_key_right(self) -> None:
        """
        Move chart to right.
        """
        self._right_ix += 1
        self._right_ix = min(self._right_ix, self._manager.get_count())

        self._update_x_range()
        self._cursor.move_right()
        self._cursor.update_info()

    def _on_key_down(self) -> None:
        """
        Zoom out the chart.
        """
        self._bar_count *= 1.2
        self._bar_count = min(int(self._bar_count), self._manager.get_count())

        self._update_x_range()
        self._cursor.update_info()

    def _on_key_up(self) -> None:
        """
        Zoom in the chart.
        """
        self._bar_count /= 1.2
        self._bar_count = max(int(self._bar_count), self.MIN_BAR_COUNT)

        self._update_x_range()
        self._cursor.update_info()

    def move_to_right(self) -> None:
        """
        Move chart to the most right.
        """
        self._right_ix = self._manager.get_count()
        self._update_x_range()
        #self._cursor.update_info()

class ChartCursor(QtCore.QObject):
    """"""

    def __init__(
        self,
        widget: ChartWidget,
        manager: BarManager,
        plots: Dict[str, pg.GraphicsObject],
        item_plot_map: Dict[ChartItem, pg.GraphicsObject]
    ):
        """"""
        super().__init__()

        self._widget: ChartWidget = widget
        self._manager: BarManager = manager
        self._plots: Dict[str, pg.GraphicsObject] = plots
        self._item_plot_map: Dict[ChartItem, pg.GraphicsObject] = item_plot_map

        self._x: int = 0
        self._y: int = 0
        self._plot_name: str = ""

        self._init_ui()
        self._connect_signal()

    def _init_ui(self):
        """"""
        self._init_line()
        self._init_label()
        self._init_info()

    def _init_line(self) -> None:
        """
        Create line objects.
        """
        self._v_lines: Dict[str, pg.InfiniteLine] = {}
        self._h_lines: Dict[str, pg.InfiniteLine] = {}
        self._views: Dict[str, pg.ViewBox] = {}

        pen = pg.mkPen(WHITE_COLOR)

        for plot_name, plot in self._plots.items():
            v_line = pg.InfiniteLine(angle=90, movable=False, pen=pen)
            h_line = pg.InfiniteLine(angle=0, movable=False, pen=pen)
            view = plot.getViewBox()

            for line in [v_line, h_line]:
                line.setZValue(0)
                line.hide()
                view.addItem(line)

            self._v_lines[plot_name] = v_line
            self._h_lines[plot_name] = h_line
            self._views[plot_name] = view

    def _init_label(self) -> None:
        """
        Create label objects on axis.
        """
        self._y_labels: Dict[str, pg.TextItem] = {}
        for plot_name, plot in self._plots.items():
            label = pg.TextItem(
                plot_name, fill=CURSOR_COLOR, color=BLACK_COLOR)
            label.hide()
            label.setZValue(2)
            label.setFont(NORMAL_FONT)
            plot.addItem(label, ignoreBounds=True)
            self._y_labels[plot_name] = label

        self._x_label: pg.TextItem = pg.TextItem(
            "datetime", fill=CURSOR_COLOR, color=BLACK_COLOR)
        self._x_label.hide()
        self._x_label.setZValue(2)
        self._x_label.setFont(NORMAL_FONT)
        plot.addItem(self._x_label, ignoreBounds=True)

    def _init_info(self) -> None:
        """
        """
        self._infos: Dict[str, pg.TextItem] = {}
        for plot_name, plot in self._plots.items():
            info = pg.TextItem(
                "info",
                color=CURSOR_COLOR,
                border=CURSOR_COLOR,
                fill=BLACK_COLOR
            )
            info.hide()
            info.setZValue(2)
            info.setFont(NORMAL_FONT)
            plot.addItem(info)  # , ignoreBounds=True)
            self._infos[plot_name] = info

    def _connect_signal(self) -> None:
        """
        Connect mouse move signal to update function.
        """
        self._widget.scene().sigMouseMoved.connect(self._mouse_moved)

    def _mouse_moved(self, evt: tuple) -> None:
        """
        Callback function when mouse is moved.
        """
        if not self._manager.get_count():
            return

        # First get current mouse point
        pos = evt

        for plot_name, view in self._views.items():
            rect = view.sceneBoundingRect()

            if rect.contains(pos):
                mouse_point = view.mapSceneToView(pos)
                self._x = to_int(mouse_point.x())
                self._y = mouse_point.y()
                self._plot_name = plot_name
                break

        # Then update cursor component
        self._update_line()
        self._update_label()
        self.update_info()

    def _update_line(self) -> None:
        """"""
        for v_line in self._v_lines.values():
            v_line.setPos(self._x)
            v_line.show()

        for plot_name, h_line in self._h_lines.items():
            if plot_name == self._plot_name:
                h_line.setPos(self._y)
                h_line.show()
            else:
                h_line.hide()

    def _update_label(self) -> None:
        """"""
        bottom_plot = list(self._plots.values())[-1]
        axis_width = bottom_plot.getAxis("right").width()
        axis_height = bottom_plot.getAxis("bottom").height()
        axis_offset = QtCore.QPointF(axis_width, axis_height)

        bottom_view = list(self._views.values())[-1]
        bottom_right = bottom_view.mapSceneToView(
            bottom_view.sceneBoundingRect().bottomRight() - axis_offset
        )

        for plot_name, label in self._y_labels.items():
            if plot_name == self._plot_name:
                label.setText(str(self._y))
                label.show()
                label.setPos(bottom_right.x(), self._y)
            else:
                label.hide()

        dt = self._manager.get_datetime(self._x)
        if dt:
            self._x_label.setText(dt.strftime("%H:%M:%S"))
            self._x_label.show()
            self._x_label.setPos(self._x, bottom_right.y())
            self._x_label.setAnchor((0, 0))

    def update_info(self) -> None:
        """"""
        buf = {}
        for item, plot in self._item_plot_map.items():
            item_info_text = item.get_info_text(self._x)

            if plot not in buf:
                buf[plot] = item_info_text
            else:
                if item_info_text:
                    buf[plot] += ("\n\n" + item_info_text)
        for plot_name, plot in self._plots.items():
            plot_info_text = buf[plot]
            info = self._infos[plot_name]
            info.setText(plot_info_text)
            info.show()
            view = self._views[plot_name]
            top_left = view.mapSceneToView(view.sceneBoundingRect().topLeft())
            info.setPos(top_left)

    def move_right(self) -> None:
        """
        Move cursor index to right by 1.
        """
        if self._x == self._manager.get_count() - 1:
            return
        self._x += 1

        self._update_after_move()

    def move_left(self) -> None:
        """
        Move cursor index to left by 1.
        """
        if self._x == 0:
            return
        self._x -= 1

        self._update_after_move()

    def _update_after_move(self) -> None:
        """
        Update cursor after moved by left/right.
        """
        bar = self._manager.get_bar(self._x)
        self._y = bar.close_price

        self._update_line()
        self._update_label()

    def clear_all(self) -> None:
        """
        Clear all data.
        """
        self._x = 0
        self._y = 0
        self._plot_name = ""

        for line in list(self._v_lines.values()) + list(self._h_lines.values()):
            line.hide()

        for label in list(self._y_labels.values()) + [self._x_label]:
            label.hide()

        
class CFtdcMdSpi(mdapi.CThostFtdcMdSpi):
    tapi=None
    def __init__(self,tapi, widget : ChartWidget):
        mdapi.CThostFtdcMdSpi.__init__(self)
        self.tapi=tapi
        self.bar = None
        self.lastVolume : double = 0
        self.widget = widget

    def OnFrontConnected(self) -> "void":
        print ("OnFrontConnected")
        loginfield = mdapi.CThostFtdcReqUserLoginField()
        loginfield.BrokerID="8000"
        loginfield.UserID="000005"
        loginfield.Password="123456"
        loginfield.UserProductInfo="python dll"
        self.tapi.ReqUserLogin(loginfield,0)
    def OnRspUserLogin(self, pRspUserLogin: 'CThostFtdcRspUserLoginField', pRspInfo: 'CThostFtdcRspInfoField', nRequestID: 'int', bIsLast: 'bool') -> "void":
        print ("OnRspUserLogin")
        print ("SessionID=",pRspUserLogin. SessionID)
        print ("ErrorID=",pRspInfo.ErrorID)
        print ("ErrorMsg=",pRspInfo.ErrorMsg)
        ret=self.tapi.SubscribeMarketData([b"rb1910"],1)

    def OnRtnDepthMarketData(self, pDepthMarketData: 'CThostFtdcDepthMarketDataField') -> "void":       
        if not pDepthMarketData:
            return;     
        st= pDepthMarketData.UpdateTime.split(':')       
        if not self.bar:
            newMinitue = True
        else:
            if int(st[1]) == self.bar.updateTime.minute :
                newMinitue = False
            else:
                newMinitue = True
        if newMinitue :
            self.bar = CBarData()
            self.bar.instrumentID = pDepthMarketData.InstrumentID
            self.bar.exchangeID = pDepthMarketData.ExchangeID
            self.bar.updateTime = time(int(st[0]),int(st[1]),0,0)
            self.bar.volume = 0
            self.bar.openInterest = pDepthMarketData.OpenInterest
            self.bar.openPrice = pDepthMarketData.LastPrice
            self.bar.highPrice = pDepthMarketData.LastPrice
            self.bar.lowPrice = pDepthMarketData.LastPrice
            self.bar.closePrice = pDepthMarketData.LastPrice
        else :
            self.bar.highPrice = max(self.bar.highPrice, pDepthMarketData.LastPrice)
            self.bar.lowPrice = min(self.bar.lowPrice, pDepthMarketData.LastPrice)
            self.bar.closePrice = pDepthMarketData.LastPrice
            self.bar.openInterest = pDepthMarketData.OpenInterest
        
        if not self.lastVolume:
            self.bar.volume += max(pDepthMarketData.Volume-self.lastVolume,0)
        self.lastVolume = pDepthMarketData.Volume
        if self.bar.closePrice > self.bar.openPrice :
            str = "red"
        else :
            str = "green"
        print(f"bar:{self.bar.updateTime},O[{self.bar.openPrice}],H[{self.bar.highPrice}],L[{self.bar.lowPrice}],C[{self.bar.closePrice}],color:[ {str} ]")
        self.widget.update_bar(self.bar)
        

    def OnRspSubMarketData(self, pSpecificInstrument: 'CThostFtdcSpecificInstrumentField', pRspInfo: 'CThostFtdcRspInfoField', nRequestID: 'int', bIsLast: 'bool') -> "void":
        print ("OnRspSubMarketData")
        print ("InstrumentID=",pSpecificInstrument.InstrumentID)
        print ("ErrorID=",pRspInfo.ErrorID)
        print ("ErrorMsg=",pRspInfo.ErrorMsg)




def main():

    app = QtWidgets.QApplication([])
    widget = ChartWidget()

    mduserapi=mdapi.CThostFtdcMdApi_CreateFtdcMdApi()
    mduserspi=CFtdcMdSpi(mduserapi,widget)
    #mduserapi.RegisterFront("tcp://101.230.209.178:53313")
    '''以下是7*24小时环境'''
    mduserapi.RegisterFront("tcp://180.168.146.187:10131")
    mduserapi.RegisterSpi(mduserspi)
    mduserapi.Init()

    widget.add_plot("candle")
    widget.add_item(CandleItem, "candle", "candle")
    widget.add_cursor()
    widget.show()
    app.exec_()


    mduserapi.Join()

if __name__ == '__main__':
    main()