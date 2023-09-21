import ipywidgets.widgets as W
import traitlets

import numpy as np


def check_ipywidget_backend():
    import matplotlib

    mpl_backend = matplotlib.get_backend()
    assert "ipympl" in mpl_backend, "To use the 'ipywidgets' backend, you have to set %matplotlib widget"


def make_timeseries_controller(t_start, t_stop, layer_keys, num_segments, time_range, mode, all_layers, width_cm):
    time_slider = W.FloatSlider(
        orientation="horizontal",
        description="time:",
        value=time_range[0],
        min=t_start,
        max=t_stop,
        continuous_update=False,
        layout=W.Layout(width=f"{width_cm}cm"),
    )
    layer_selector = W.Dropdown(description="layer", options=layer_keys)
    segment_selector = W.Dropdown(description="segment", options=list(range(num_segments)))
    window_sizer = W.BoundedFloatText(value=np.diff(time_range)[0], step=0.1, min=0.005, description="win (s)")
    mode_selector = W.Dropdown(options=["line", "map"], description="mode", value=mode)
    all_layers = W.Checkbox(description="plot all layers", value=all_layers)

    controller = {
        "layer_key": layer_selector,
        "segment_index": segment_selector,
        "window": window_sizer,
        "t_start": time_slider,
        "mode": mode_selector,
        "all_layers": all_layers,
    }
    widget = W.VBox(
        [time_slider, W.HBox([all_layers, layer_selector, segment_selector, window_sizer, mode_selector])]
    )

    return widget, controller


def make_unit_controller(unit_ids, all_unit_ids, width_cm, height_cm):
    unit_label = W.Label(value="units:")

    unit_selector = W.SelectMultiple(
        options=all_unit_ids,
        value=list(unit_ids),
        disabled=False,
        layout=W.Layout(width=f"{width_cm}cm", height=f"{height_cm}cm"),
    )

    controller = {"unit_ids": unit_selector}
    widget = W.VBox([unit_label, unit_selector])

    return widget, controller


def make_channel_controller(recording, width_cm, height_cm):
    channel_label = W.Label("channel indices:", layout=W.Layout(justify_content="center"))
    channel_selector = W.IntRangeSlider(
        value=[0, recording.get_num_channels()],
        min=0,
        max=recording.get_num_channels(),
        step=1,
        disabled=False,
        continuous_update=False,
        orientation="vertical",
        readout=True,
        readout_format="d",
        layout=W.Layout(width=f"{0.8 * width_cm}cm", height=f"{height_cm}cm"),
    )

    controller = {"channel_inds": channel_selector}
    widget = W.VBox([channel_label, channel_selector])

    return widget, controller


def make_scale_controller(width_cm, height_cm):
    scale_label = W.Label("Scale", layout=W.Layout(justify_content="center"))

    plus_selector = W.Button(
        description="",
        disabled=False,
        button_style="",  # 'success', 'info', 'warning', 'danger' or ''
        tooltip="Increase scale",
        icon="arrow-up",
        layout=W.Layout(width=f"{0.8 * width_cm}cm", height=f"{0.4 * height_cm}cm"),
    )

    minus_selector = W.Button(
        description="",
        disabled=False,
        button_style="",  # 'success', 'info', 'warning', 'danger' or ''
        tooltip="Decrease scale",
        icon="arrow-down",
        layout=W.Layout(width=f"{0.8 * width_cm}cm", height=f"{0.4 * height_cm}cm"),
    )

    controller = {"plus": plus_selector, "minus": minus_selector}
    widget = W.VBox([scale_label, plus_selector, minus_selector])

    return widget, controller



class TimeSlider(W.HBox):

    position = traitlets.Tuple(traitlets.Int(), traitlets.Int(), traitlets.Int())
    
    def __init__(self, durations, sampling_frequency, time_range=(0, 1.), **kwargs):
        
        
        self.num_segments = len(durations)
        self.frame_limits = [int(sampling_frequency * d) for d in durations]
        self.sampling_frequency = sampling_frequency
        start_frame = int(time_range[0] * sampling_frequency)
        end_frame = int(time_range[1] * sampling_frequency)

        self.frame_range = (start_frame, end_frame)

        self.segment_index = 0
        self.position = (start_frame, end_frame, self.segment_index)
        
        
        layout = W.Layout(align_items="center", width="1.5cm", height="100%")
        but_left = W.Button(description='', disabled=False, button_style='', icon='arrow-left', layout=layout)
        but_right = W.Button(description='', disabled=False, button_style='', icon='arrow-right', layout=layout)
        
        but_left.on_click(self.move_left)
        but_right.on_click(self.move_right)

        self.move_size = W.Dropdown(options=['10 ms', '100 ms', '1 s', '10 s', '1 m', '30 m', '1 h',],  #  '6 h', '24 h'
                                    value='1 s',
                                    description='',
                                    layout = W.Layout(width="2cm")
                                    )

        # DatetimePicker is only for ipywidget v8 (which is not working in vscode 2023-03)
        self.time_label = W.Text(value=f'{time_range[0]}',description='',
                                 disabled=False, layout=W.Layout(width='5.5cm'))
        self.time_label.observe(self.time_label_changed, names='value', type="change")


        self.slider = W.IntSlider(
            orientation='horizontal',
            # description='time:',
            value=start_frame,
            min=0,
            max=self.frame_limits[self.segment_index],
            readout=False,
            continuous_update=False,
            layout=W.Layout(width=f'70%')
        )
        
        self.slider.observe(self.slider_moved, names='value', type="change")
        
        delta_s = np.diff(self.frame_range) / sampling_frequency
        
        self.window_sizer = W.BoundedFloatText(value=delta_s, step=1,
                                        min=0.01, max=30.,
                                        description='win (s)',
                                        layout=W.Layout(width='auto')
                                        # layout=W.Layout(width=f'10%')
                                        )
        self.window_sizer.observe(self.win_size_changed, names='value', type="change")

        self.segment_selector = W.Dropdown(description="segment", options=list(range(self.num_segments)))
        self.segment_selector.observe(self.segment_changed, names='value', type="change")

        super(W.HBox, self).__init__(children=[self.segment_selector, but_left, self.move_size, but_right,
                                               self.slider, self.time_label, self.window_sizer],
                                     layout=W.Layout(align_items="center", width="100%", height="100%"),
                                     **kwargs)
        
        self.observe(self.position_changed, names=['position'], type="change")

    def position_changed(self, change=None):

        self.unobserve(self.position_changed, names=['position'], type="change")

        start, stop, seg_index = self.position
        if seg_index < 0 or seg_index >= self.num_segments:
            self.position = change['old']
            return
        if start < 0 or stop < 0:
            self.position = change['old']
            return
        if start >= self.frame_limits[seg_index] or start > self.frame_limits[seg_index]:
            self.position = change['old']
            return
        
        self.segment_selector.value = seg_index
        self.update_time(new_frame=start, update_slider=True, update_label=True)
        delta_s = (stop - start) / self.sampling_frequency
        self.window_sizer.value = delta_s

        self.observe(self.position_changed, names=['position'], type="change")

    def update_time(self, new_frame=None, new_time=None, update_slider=False, update_label=False):
        if new_frame is None and new_time is None:
            start_frame = self.slider.value
        elif new_frame is None:
            start_frame = int(new_time * self.sampling_frequency)
        else:
            start_frame = new_frame
        delta_s = self.window_sizer.value
        end_frame = start_frame + int(delta_s * self.sampling_frequency)
        
        # clip
        start_frame = max(0, start_frame)
        end_frame = min(self.frame_limits[self.segment_index], end_frame)

        
        start_time = start_frame / self.sampling_frequency

        if update_label:
            self.time_label.unobserve(self.time_label_changed, names='value', type="change")
            self.time_label.value = f'{start_time}'
            self.time_label.observe(self.time_label_changed, names='value', type="change")

        if update_slider:
            self.slider.unobserve(self.slider_moved, names='value', type="change")
            self.slider.value = start_frame
            self.slider.observe(self.slider_moved, names='value', type="change")
        
        self.frame_range = (start_frame, end_frame)
        
    def time_label_changed(self, change=None):
        try:
            new_time = float(self.time_label.value)
        except:
            new_time = None
        if new_time is not None:
            self.update_time(new_time=new_time, update_slider=True)


    def win_size_changed(self, change=None):
        self.update_time()
        
    def slider_moved(self, change=None):
        new_frame = self.slider.value
        self.update_time(new_frame=new_frame, update_label=True)
    
    def move(self, sign):
        value, units = self.move_size.value.split(' ')
        value = int(value)
        delta_s = (sign * np.timedelta64(value, units)) / np.timedelta64(1, 's')
        delta_sample = int(delta_s * self.sampling_frequency)

        new_frame = self.frame_range[0] + delta_sample
        self.slider.value = new_frame
    
    def move_left(self, change=None):
        self.move(-1)

    def move_right(self, change=None):
        self.move(+1)
    
    def segment_changed(self, change=None):
        self.segment_index = self.segment_selector.value

        self.slider.unobserve(self.slider_moved, names='value', type="change")
        # self.slider.value = 0
        self.slider.max = self.frame_limits[self.segment_index]
        self.slider.observe(self.slider_moved, names='value', type="change")

        self.update_time(new_frame=0, update_slider=True, update_label=True)



class ScaleWidget(W.VBox):
    def __init__(self, **kwargs):
        scale_label = W.Label("Scale",
                              layout=W.Layout(layout=W.Layout(width='95%'),
                                              justify_content="center"))

        self.plus_selector = W.Button(
            description="",
            disabled=False,
            button_style="",  # 'success', 'info', 'warning', 'danger' or ''
            tooltip="Increase scale",
            icon="arrow-up",
            # layout=W.Layout(width=f"{0.8 * width_cm}cm", height=f"{0.4 * height_cm}cm"),
            layout=W.Layout(width='95%'),
        )

        self.minus_selector = W.Button(
            description="",
            disabled=False,
            button_style="",  # 'success', 'info', 'warning', 'danger' or ''
            tooltip="Decrease scale",
            icon="arrow-down",
            # layout=W.Layout(width=f"{0.8 * width_cm}cm", height=f"{0.4 * height_cm}cm"),
            layout=W.Layout(width='95%'),
        )

        # controller = {"plus": plus_selector, "minus": minus_selector}
        # widget = W.VBox([scale_label, plus_selector, minus_selector])


        super(W.VBox, self).__init__(children=[scale_label, self.plus_selector, self.minus_selector],
                                    #  layout=W.Layout(align_items="center", width="100%", height="100%"),
                                     **kwargs)
