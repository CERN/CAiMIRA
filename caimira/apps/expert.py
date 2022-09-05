import dataclasses
import typing
import uuid

import ipympl.backend_nbagg
import ipywidgets as widgets
import matplotlib
import matplotlib.figure
import matplotlib.lines as mlines
import matplotlib.patches as patches
from matplotlib import pyplot as plt
import numpy as np

from caimira import data, models, state    


def collapsible(widgets_to_collapse: typing.List, title: str, start_collapsed=False):
    collapsed = widgets.Accordion([widgets.VBox(widgets_to_collapse)])
    collapsed.set_title(0, title)
    if start_collapsed:
        collapsed.selected_index = None
    return collapsed


def widget_group(label_widget_pairs):
    labels, widgets_ = zip(*label_widget_pairs)
    labels_w = widgets.VBox(labels)
    widgets_w = widgets.VBox(widgets_)
    return widgets.VBox([widgets.HBox([labels_w, widgets_w])])


WidgetPairType = typing.Tuple[widgets.Widget, widgets.Widget]


class WidgetGroup:
    def __init__(self, label_widget_pairs: typing.Iterable[WidgetPairType]):
        self.labels: typing.List[widgets.Widget] = []
        self.widgets: typing.List[widgets.Widget] = []
        self.add_pairs(label_widget_pairs)

    def set_visible(self, visible: bool):
        for widget in (self.labels + self.widgets):
            if visible:
                widget.layout.visible = True
                widget.layout.display = 'flex'
            else:
                widget.layout.visible = False
                widget.layout.display = 'none'

    def pairs(self) -> typing.Iterable[WidgetPairType]:
        return zip(*[self.labels, self.widgets])

    def add_pairs(self, label_widget_pairs: typing.Iterable[WidgetPairType]):
        labels, widgets_ = zip(*label_widget_pairs)
        self.labels.extend(labels)
        self.widgets.extend(widgets_)

    def build(self):
        labels_w = widgets.VBox(self.labels)
        widgets_w = widgets.VBox(self.widgets)
        return widgets.VBox(
            [
                widgets.HBox(
                    [labels_w, widgets_w], layout=widgets.Layout(justify_content='space-between')
                ),
            ],
        )


#: A scenario is a name and a (mutable) model.
ScenarioType = typing.Tuple[str, state.DataclassState]


class View:
    """
    A thing which exposes a ``.widget`` attribute which is a view on some
    data. This view is essentially a complex combination of widgets, along with
    some event handling capabilities, which may or may not be sent back up to
    the underlying controller.

    We strive hard to keep "Model" data out of the View (and try to avoid
    storing it at all on the View itself), instead relying on being able
    to notify, and receive notifications, of important events from the Controller.

    """
    pass


class Controller:
    """
    The singleton thing which is the top-level Application.

    It is responsible for owning the Model data and the Views, and
    orchestrating event messages to each if the Model/View change.

    """
    pass


def ipympl_canvas(figure):
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    matplotlib.interactive(False)
    ipympl.backend_nbagg.new_figure_manager_given_figure(hash(uuid.uuid1()), figure)
    figure.canvas.toolbar_visible = True
    figure.canvas.toolbar.collapsed = True
    figure.canvas.footer_visible = False
    figure.canvas.header_visible = False
    return figure.canvas


class ExposureModelResult(View):
    def __init__(self):
        self.figure = matplotlib.figure.Figure(figsize=(9, 6))
        ipympl_canvas(self.figure)
        self.html_output = widgets.HTML()
        self.ax, self.ax2 = self.initialize_axes()
        self.concentration_line = None
        self.concentration_area = None
        self.cumulative_line = None

    @property
    def widget(self):
        return widgets.VBox([
            self.html_output,
            self.figure.canvas,
        ])

    def initialize_axes(self) -> matplotlib.figure.Axes:
        ax = self.figure.add_subplot(1, 1, 1)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.set_xlabel('Time (hours)')
        ax.set_ylabel('Mean concentration ($virions/m^{3}$)')
        ax.set_title('Concentration of virions \nand Cumulative dose')

        ax2 = ax.twinx() 
        ax2.spines['left'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        ax2.set_ylabel('Mean cumulative dose (infectious virus)')
        ax2.spines['right'].set_linestyle((0,(1,4)))
        
        return ax, ax2

    def update(self, model: models.ExposureModel):
        self.update_plot(model)
        self.update_textual_result(model)

    def update_plot(self, model: models.ExposureModel):
        resolution = 600
        ts = np.linspace(sorted(model.concentration_model.infected.presence.transition_times())[0],
                         sorted(model.concentration_model.infected.presence.transition_times())[-1], resolution)
        concentration = [model.concentration(t) for t in ts]
        
        cumulative_doses = np.cumsum([
            np.array(model.deposited_exposure_between_bounds(float(time1), float(time2))).mean()
            for time1, time2 in zip(ts[:-1], ts[1:])
        ])

        if self.concentration_line is None:
            [self.concentration_line] = self.ax.plot(ts, concentration, color='#3530fe')

        else:
            self.ax.ignore_existing_data_limits = False
            self.concentration_line.set_data(ts, concentration)
        
        if self.concentration_area is None:
            self.concentration_area = self.ax.fill_between(x = ts, y1=0, y2=concentration, color="#96cbff",
                where = ((model.exposed.presence.boundaries()[0][0] < ts) & (ts < model.exposed.presence.boundaries()[0][1]) | 
                    (model.exposed.presence.boundaries()[1][0] < ts) & (ts < model.exposed.presence.boundaries()[1][1])))
                   
        else:
            self.concentration_area.remove()         
            self.concentration_area = self.ax.fill_between(x = ts, y1=0, y2=concentration, color="#96cbff",
                where = ((model.exposed.presence.boundaries()[0][0] < ts) & (ts < model.exposed.presence.boundaries()[0][1]) | 
                    (model.exposed.presence.boundaries()[1][0] < ts) & (ts < model.exposed.presence.boundaries()[1][1])))

        if self.cumulative_line is None:
            [self.cumulative_line] = self.ax2.plot(ts[:-1], cumulative_doses, color='#0000c8', linestyle='dotted')
            
        else:
            self.ax2.ignore_existing_data_limits = False
            self.cumulative_line.set_data(ts[:-1], cumulative_doses)

        concentration_top = max(np.array(concentration))
        self.ax.set_ylim(bottom=0., top=concentration_top)
        cumulative_top = max(cumulative_doses)
        self.ax2.set_ylim(bottom=0., top=cumulative_top)

        self.ax.set_xlim(left = min(min(model.concentration_model.infected.presence.boundaries()[0]), min(model.exposed.presence.boundaries()[0])), 
                        right = max(max(model.concentration_model.infected.presence.boundaries()[1]), max(model.exposed.presence.boundaries()[1])))
   
        figure_legends = [mlines.Line2D([], [], color='#3530fe', markersize=15, label='Mean concentration'),
                   mlines.Line2D([], [], color='#0000c8', markersize=15, ls="dotted", label='Cumulative dose'),
                   patches.Patch(edgecolor="#96cbff", facecolor='#96cbff', label='Presence of exposed person(s)')]
        self.ax.legend(handles=figure_legends)

        self.figure.canvas.draw()

    def update_textual_result(self, model: models.ExposureModel):
        lines = []
        P = np.array(model.infection_probability()).mean()
        lines.append(f'Emission rate (virus/hr): {np.round(model.concentration_model.infected.emission_rate_when_present(),0)}')
        lines.append(f'Probability of infection: {np.round(P, 0)}%')

        lines.append(f'Number of exposed: {model.exposed.number}')

        new_cases = np.round(np.array(model.expected_new_cases()).mean(), 1)
        lines.append(f'Number of expected new cases: {new_cases}')

        R0 = np.round(np.array(model.reproduction_number()).mean(), 1)
        lines.append(f'Reproduction number (R0): {R0}')

        self.html_output.value = '<br>\n'.join(lines)    


class ExposureComparissonResult(View):
    def __init__(self):
        self.figure = matplotlib.figure.Figure(figsize=(9, 6))
        ipympl_canvas(self.figure)
        self.html_output = widgets.HTML()
        self.ax, self.ax2 = self.initialize_axes()

    @property
    def widget(self):
        # Workaround to a bug with ipymlp, which doesn't work well with tabs
        # unless the widget is wrapped in a container (it is seen on all tabs otherwise!).
        return widgets.HBox([self.figure.canvas])

    def initialize_axes(self) -> matplotlib.figure.Axes:
        ax = self.figure.add_subplot(1, 1, 1)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        
        ax.set_xlabel('Time (hours)')
        ax.set_ylabel('Mean concentration ($virions/m^{3}$)')
        ax.set_title('Concentration of virions \nand Cumulative dose')
        
        ax2 = ax.twinx()
        ax2.spines['left'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_linestyle((0,(1,4)))

        ax2.set_ylabel('Mean cumulative dose (infectious virus)')

        return ax, ax2

    def scenarios_updated(self, scenarios: typing.Sequence[ScenarioType], _):
        updated_labels, updated_models = zip(*scenarios)
        exp_models = tuple(
            model.dcs_instance() for model in updated_models
        )
        self.update_plot(exp_models, updated_labels)

    def update_plot(self, exp_models: typing.Tuple[models.ExposureModel, ...], labels: typing.Tuple[str, ...]):
        [line.remove() for line in self.ax.lines]
        [line.remove() for line in self.ax2.lines]
        start, finish = models_start_end(exp_models)
        colors=['blue', 'red', 'orange', 'yellow', 'pink', 'purple', 'green', 'brown', 'black' ]
        ts = np.linspace(start, finish, num=250)
        concentrations = [[conc_model.concentration_model.concentration(t) for t in ts] for conc_model in exp_models]
        for label, concentration, color in zip(labels, concentrations, colors):
            self.ax.plot(ts, concentration, label=label, color=color)
            
        cumulative_doses = [np.cumsum([
            np.array(conc_model.deposited_exposure_between_bounds(float(time1), float(time2))).mean()
            for time1, time2 in zip(ts[:-1], ts[1:])
        ]) for conc_model in exp_models]
        
        for label, cumulative_dose, color in zip(labels, cumulative_doses, colors):
            self.ax2.plot(ts[:-1], cumulative_dose, label=label, color=color, linestyle="dotted")
            
        concentration_top = max([max(np.array(concentration)) for concentration in concentrations])
        self.ax.set_ylim(bottom=0., top=concentration_top)
        cumulative_top = max([max(cumulative_dose) for cumulative_dose in cumulative_doses])
        self.ax2.set_ylim(bottom=0., top=cumulative_top)

        self.ax.legend()
        self.figure.canvas.draw()


class ModelWidgets(View):
    def __init__(self, model_state: state.DataclassState):
        #: The widgets that this view produces (inputs and outputs together)
        self.widget = widgets.VBox([])
        self.construct_widgets(model_state)

    def construct_widgets(self, model_state: state.DataclassState):
        # Build the input widgets.
        self._build_widget(model_state)

    def _build_widget(self, node):
        self.widget.children += (self._build_room(node.concentration_model.room),)
        self.widget.children += (self._build_ventilation(node.concentration_model.ventilation),)
        self.widget.children += (self._build_infected(node.concentration_model.infected, node.concentration_model.ventilation),)
        self.widget.children += (self._build_exposed(node),)
        
    def _build_exposed(self, node):
        return collapsible([widgets.VBox([
            self._build_exposed_number(node.exposed),
            self._build_mask(node.exposed.mask),
            self._build_activity(node.exposed.activity),
            self._build_exposed_presence(node.exposed.presence)
        ])], title="Exposed")

    def _build_infected(self, node, ventilation_node):
        return collapsible([widgets.VBox([
            self._build_infected_number(node),
            self._build_mask(node.mask),
            self._build_activity(node.activity),
            self._build_expiration(node.expiration),
            self._build_viral_load(node.virus),
            self._build_infected_presence(node.presence, ventilation_node.active),
            self._build_infectivity(node)
        ])], title="Infected")

    def _build_room_volume(self, node):
        room_volume = widgets.BoundedIntText(value=node.volume, min=10, max=500, step=5)

        def on_volume_change(change):
            node.volume = change['new']

        # TODO: Link the state back to the widget, not just the other way around.
        room_volume.observe(on_volume_change, names=['value'])
    
        return widgets.HBox([widgets.Label('Room volume (m³)'), room_volume], layout=widgets.Layout(justify_content='space-between'))


    def _build_room_area(self, node):
        room_surface = widgets.BoundedIntText(value=25, min=1, max=200, step=10)
        room_ceiling_height = widgets.BoundedFloatText(value=3.5, min=1, max=10, step=0.1)
        displayed_volume=widgets.Label('75')

        def on_room_surface_change(change):
            node.volume = change['new']*room_ceiling_height.value 
            displayed_volume.value=str(node.volume)

        def on_room_ceiling_height_change(change):
            node.volume = change['new']*room_surface.value 
            displayed_volume.value=str(node.volume)

        room_surface.observe(on_room_surface_change, names=['value'])
        room_ceiling_height.observe(on_room_ceiling_height_change, names=['value'])        

        return widgets.VBox([widgets.HBox([widgets.Label('Room surface area (m²) '), room_surface],
        layout=widgets.Layout(justify_content='space-between', width='100%')),
        widgets.HBox([widgets.Label('Room ceiling height (m)'), room_ceiling_height],
        layout=widgets.Layout(justify_content='space-between', width='100%')),
        widgets.HBox([widgets.Label('Total volume :'), displayed_volume, widgets.Label('m³')])])

    def _build_room(self,node):
        room_number = widgets.Text(value='', placeholder='653/R-004', disabled=False) #not linked to volume yet
        room_widgets={
            'Volume': self._build_room_volume(node),
            'Room area and height': self._build_room_area(node)
        }

        for name, widget in room_widgets.items():
            widget.layout.visible = False
            widget.layout.display = 'none'

        room_w = widgets.RadioButtons(
            options= list(zip(['Volume', 'Room area and height'], room_widgets.keys())),
            layout=widgets.Layout(height='auto', width='auto'),
        )

        def toggle_room(value):
            for name, widget in room_widgets.items():
                widget.layout.visible = False
                widget.layout.display = 'none'

            widget = room_widgets[value]
            widget.layout.visible = True
            widget.layout.display = 'flex'

        room_w.observe(lambda event: toggle_room(event['new']), 'value')
        toggle_room(room_w.value)

        humidity = widgets.FloatSlider(value = node.humidity*100, min=20, max=80, step=5)
        inside_temp = widgets.IntSlider(value=node.inside_temp.values[0]-273.15, min=15., max=25.)

        def on_humidity_change(change):
            node.humidity = change['new']/100

        def on_insidetemp_change(change):
            node.inside_temp.values = (change['new']+273.15,)

        humidity.observe(on_humidity_change, names=['value'])
        inside_temp.observe(on_insidetemp_change, names=['value'])

        widget = collapsible(
            [ widgets.VBox([
                widgets.HBox([
                    widgets.Label('Room number'), room_number],
                    layout=widgets.Layout(width='100%', justify_content='space-between')),
            room_w, widgets.VBox(list(room_widgets.values())),
            widgets.HBox([widgets.Label('Inside temperature (℃)'), inside_temp],
            layout=widgets.Layout(width='100%', justify_content='space-between')),
            widgets.HBox([widgets.Label('Indoor relative humidity (%)'), humidity],
            layout=widgets.Layout(width='100%', justify_content='space-between')),
            ])]
            , title="Specification of workspace"
        )

        return widget

    def _build_outsidetemp(self, node) -> WidgetGroup:
        outside_temp = widgets.IntSlider(value=10, min=-10, max=30)

        def on_outsidetemp_change(change):
            node.values = (change['new'] + 273.15, )

        outside_temp.observe(on_outsidetemp_change, names=['value'])
        auto_width = widgets.Layout(width='auto')
        return WidgetGroup(
            (
                (
                    widgets.Label('Outside temperature (℃)', layout=auto_width,),
                    outside_temp,
                ),
            ),
        )

    def _build_hinged_window(self, node):
            hinged_window = widgets.FloatSlider(value=node.window_width, min=0.1, max=2, step=0.1)

            def on_hinged_window_change(change):
                node.window_width = change['new']

            # TODO: Link the state back to the widget, not just the other way around.
            hinged_window.observe(on_hinged_window_change, names=['value'])
            
            return widgets.HBox([widgets.Label('Window width (meters) '), hinged_window], layout=widgets.Layout(justify_content='space-between', width='100%'))

    def _build_sliding_window(self, node):
        return widgets.HBox([]) 

    def _build_window(self, node) -> WidgetGroup:
        window_widgets = {
            'Natural': self._build_sliding_window(node._states['Natural']),
            'Hinged window': self._build_hinged_window(node._states['Hinged window']), 
        }

        for name, widget in window_widgets.items():
            widget.layout.visible = False
            widget.layout.display = 'none'

        window_w = widgets.RadioButtons(
            options= list(zip(['Sliding window', 'Hinged window'], window_widgets.keys())),
            layout=widgets.Layout(height='auto', width='auto'),
        )

        def toggle_window(value):
            for name, widget in window_widgets.items():
                widget.layout.visible = False
                widget.layout.display = 'none'

            node.dcs_select(value)

            widget = window_widgets[value]
            widget.layout.visible = True
            widget.layout.display = 'flex'

        window_w.observe(lambda event: toggle_window(event['new']), 'value')
        toggle_window(window_w.value)

        number_of_windows= widgets.BoundedIntText(value=1, min=1, max=10, step=1)
        period = widgets.IntSlider(value=node.active.period, min=0, max=240)
        interval = widgets.IntSlider(value=node.active.duration, min=0, max=240)
        opening_length = widgets.FloatSlider(value=node.opening_length, min=0, max=3, step=0.1)
        window_height = widgets.FloatSlider(value=node.window_height, min=0, max=3, step=0.1)

        def on_value_change(change):
            node.number_of_windows = change['new']
        
        def on_period_change(change):
            node.active.period = change['new']

        def on_interval_change(change):
            node.active.duration = change['new']

        def on_opening_length_change(change):
            node.opening_length = change['new']
        
        def on_window_height_change(change):
            node.window_height = change['new']

        # TODO: Link the state back to the widget, not just the other way around.
        number_of_windows.observe(on_value_change, names=['value'])
        period.observe(on_period_change, names=['value'])
        interval.observe(on_interval_change, names=['value'])
        opening_length.observe(on_opening_length_change, names=['value'])
        window_height.observe(on_window_height_change, names=['value'])

        outsidetemp_widgets = {
            'Fixed': self._build_outsidetemp(node.outside_temp),
            'Meteorological data': self._build_month(node),
        }

        outsidetemp_w = widgets.Dropdown(
            options=outsidetemp_widgets.keys(),
        )

        def toggle_outsidetemp(value):
            for name, widget_group in outsidetemp_widgets.items():
                widget_group.set_visible(False)

            widget_group = outsidetemp_widgets[value]
            widget_group.set_visible(True)

        outsidetemp_w.observe(lambda event: toggle_outsidetemp(event['new']), 'value')
        toggle_outsidetemp(outsidetemp_w.value)

        auto_width = widgets.Layout(width='auto', justify_content='space-between')
        result = WidgetGroup(
            (
                (
                   widgets.Label('Number of windows ', layout=auto_width), 
                   number_of_windows,
                ),                
                (
                    widgets.Label('Opening distance (meters)', layout=auto_width),
                    opening_length,
                ),
                (
                    widgets.Label('Window height (meters)', layout=auto_width),
                    window_height,
                ),
                (
                    widgets.Label('Interval between openings (minutes)', layout=auto_width),
                    period,
                ),
                (
                    widgets.Label('Duration of opening (minutes)', layout=auto_width),
                    interval,
                ),
                (
                    widgets.Label('Outside temperature scheme', layout=auto_width),
                    outsidetemp_w,
                ),
            ),
        )
        for sub_group in outsidetemp_widgets.values():
            result.add_pairs(sub_group.pairs())
        return widgets.VBox([window_w, widgets.HBox(list(window_widgets.values())), result.build()])

    def _build_q_air_mech(self, node):
        q_air_mech = widgets.FloatSlider(value=node.q_air_mech, min=0, max=5000, step=25)

        def on_q_air_mech_change(change):
            node.q_air_mech = change['new']

        # TODO: Link the state back to the widget, not just the other way around.
        q_air_mech.observe(on_q_air_mech_change, names=['value'])

        return widgets.HBox([q_air_mech, widgets.Label('m³/h')])

    def _build_ach(self, node):
        air_exch = widgets.IntSlider(value=node.air_exch, min=0, max=20, step=1)

        def on_air_exch_change(change):
            node.air_exch = change['new']

        # TODO: Link the state back to the widget, not just the other way around.
        air_exch.observe(on_air_exch_change, names=['value'])

        return widgets.HBox([air_exch, widgets.Label('h⁻¹')])

    def _build_mechanical(self, node):
        mechanical_widgets = {
            'HVACMechanical': self._build_q_air_mech(node._states['HVACMechanical']),
            'AirChange': self._build_ach(node._states['AirChange']),
        }

        for name, widget in mechanical_widgets.items():
            widget.layout.visible = False

        mechanival_w = widgets.RadioButtons(
            options=list(zip(['Air supply flow rate (m³/h)', 'Air changes per hour (h⁻¹)'], mechanical_widgets.keys())),
        )

        def toggle_mechanical(value):
            for name, widget in mechanical_widgets.items():
                widget.layout.visible = False
                widget.layout.display = 'none'

            node.dcs_select(value)
            widget = mechanical_widgets[value]
            widget.layout.visible = True
            widget.layout.display = 'flex'

        mechanival_w.observe(lambda event: toggle_mechanical(event['new']), 'value')
        toggle_mechanical(mechanival_w.value)

        return widgets.VBox([mechanival_w, widgets.HBox(list(mechanical_widgets.values()))])

    def _build_month(self, node) -> WidgetGroup:

        month_choice = widgets.Select(options=list(data.GenevaTemperatures.keys()), value='Jan')

        def on_month_change(change):
            node.outside_temp = data.GenevaTemperatures[change['new']]
        month_choice.observe(on_month_change, names=['value'])

        return WidgetGroup(
            (
                (widgets.Label("Month"), month_choice),
            ),
        )

    def _build_activity(self, node):
        activity = node.dcs_instance()
        for name, activity_ in models.Activity.types.items():
            if activity == activity_:
                break
        activity = widgets.Dropdown(options=list(models.Activity.types.keys()), value=name)
        
        def on_activity_change(change):
            act = models.Activity.types[change['new']]
            node.dcs_update_from(act)
        activity.observe(on_activity_change, names=['value'])

        return widgets.HBox([widgets.Label("Activity"), activity], layout=widgets.Layout(justify_content='space-between'))

    def _build_mask(self, node):
        mask = node.dcs_instance()

        for name, mask_ in models.Mask.types.items():
            if mask == mask_:
                break
        mask_choice = widgets.Dropdown(options=list(models.Mask.types.keys()), value=name)

        def on_mask_change(change):
            node.dcs_select(change['new'])
        mask_choice.observe(on_mask_change, names=['value'])

        return widgets.HBox([widgets.Label("Mask"), mask_choice], layout=widgets.Layout(justify_content='space-between'))

    def _build_exposed_number(self, node):
        number = widgets.IntSlider(value=node.number, min=1, max=200, step=1)

        def on_exposed_number_change(change):
            node.number = change['new']
        # TODO: Link the state back to the widget, not just the other way around.
        number.observe(on_exposed_number_change, names=['value'])

        return widgets.HBox([widgets.Label('Number of exposed people in the room '), number], layout=widgets.Layout(justify_content='space-between'))

    def _build_exposed_presence(self, node):
        presence_start = widgets.FloatRangeSlider(value = node.present_times[0], min = 8., max=13., step=0.1)
        presence_finish = widgets.FloatRangeSlider(value = node.present_times[1], min = 13., max=18., step=0.1)

        def on_presence_start_change(change):
            node.present_times = (change['new'], presence_finish.value)

        def on_presence_finish_change(change):
            node.present_times = (presence_start.value, change['new'])
        
        presence_start.observe(on_presence_start_change, names=['value'])
        presence_finish.observe(on_presence_finish_change, names=['value'])

        return widgets.HBox([widgets.Label('Exposed presence'),  presence_start, presence_finish], layout = widgets.Layout(justify_content='space-between'))

    def _build_infected_number(self, node):
        number = widgets.IntSlider(value=node.number, min=1, max=200, step=1)

        def on_infected_number_change(change):
            node.number = change['new']
        # TODO: Link the state back to the widget, not just the other way around.
        number.observe(on_infected_number_change, names=['value'])

        return widgets.HBox([widgets.Label('Number of infected people in the room '), number], layout=widgets.Layout(justify_content='space-between'))

    def _build_expiration(self, node):
        expiration = node.dcs_instance()
        for name, expiration_ in models.Expiration.types.items():
            if expiration == expiration_:
                break
        expiration_choice = widgets.Dropdown(options=list(models.Expiration.types.keys()), value=name)

        def on_expiration_change(change):
            expiration = models.Expiration.types[change['new']]
            node.dcs_update_from(expiration)
            
        expiration_choice.observe(on_expiration_change, names=['value'])
        
        return widgets.HBox([widgets.Label("Expiration"), expiration_choice], layout=widgets.Layout(justify_content='space-between'))

    def _build_viral_load(self, node):
        viral_load_in_sputum = widgets.Text(continuous_update=False, value=("{:.2e}".format(node.viral_load_in_sputum)))
        def on_viral_load_change(change):
            viral_load_in_sputum.value = "{:.2e}".format(float(change['new']))
            node.viral_load_in_sputum = float(viral_load_in_sputum.value)

        viral_load_in_sputum.observe(on_viral_load_change, names=['value'])
        
        return widgets.HBox([widgets.Label("Viral load (copies/ml)"), viral_load_in_sputum], layout=widgets.Layout(justify_content='space-between'))
    
    def _build_infected_presence(self, node, ventilation_node):
       
        presence_start = widgets.FloatRangeSlider(value = node.present_times[0], min = 8., max=13., step=0.1)
        presence_finish = widgets.FloatRangeSlider(value = node.present_times[1], min = 13., max=18., step=0.1)

        def on_presence_start_change(change):
            node.present_times = (change['new'], presence_finish.value)
            
            ventilation_node.start = change['new'][0]

        def on_presence_finish_change(change):
            node.present_times = (presence_start.value, change['new'])

        presence_start.observe(on_presence_start_change, names=['value'])
        presence_finish.observe(on_presence_finish_change, names=['value'])

        return widgets.HBox([widgets.Label('Infected presence'),  presence_start, presence_finish], layout = widgets.Layout(justify_content='space-between'))

    def _build_ventilation(
            self,
            node: typing.Union[
                state.DataclassStateNamed[models.Ventilation],
                state.DataclassStateNamed[models.MultipleVentilation],
            ],
    ) -> widgets.Widget:
        ventilation_widgets = {
            'Natural': self._build_window(node),
            'HVACMechanical': self._build_mechanical(node),
            'HEPAFilter': self._build_HEPA(node),
        }

        keys=[("Natural", "Natural"), ("Mechanical", "HVACMechanical"), ("No ventilation", "No ventilation"), ("HEPA Filter", "HEPAFilter")]

        for name, widget in ventilation_widgets.items():
            widget.layout.visible = False

        ventilation_w = widgets.Dropdown(
            options=keys,
        )

        def toggle_ventilation(value):
            for name, widget in ventilation_widgets.items():
                widget.layout.visible = False
                widget.layout.display = 'none'

            node.dcs_select(value)

            widget = ventilation_widgets[value]
            widget.layout.visible = True
            widget.layout.display = 'flex'

        ventilation_w.observe(lambda event: toggle_ventilation(event['new']), 'value')
        toggle_ventilation(ventilation_w.value)
        
        w = collapsible(
            ([widgets.HBox([widgets.Label('Ventilation type'), ventilation_w], layout=widgets.Layout(justify_content='space-between'))])
            + list(ventilation_widgets.values()),
            title='Ventilation scheme',
        )
        return w

    def _build_HEPA(
        self,
        node,
    ) -> widgets.Widget:
        
        HEPA_w = widgets.FloatSlider(value=node.q_air_mech, min=10, max=500, step=5)

        def on_value_change(change):
            node.q_air_mech=change['new']

        HEPA_w.observe(on_value_change,names= ['value'])

        return widgets.HBox([widgets.Label('HEPA Filtration (m³/h) '),HEPA_w], layout=widgets.Layout(justify_content='space-between'))

    def _build_infectivity(self, node):
        return collapsible([widgets.VBox([
            self._build_virus(node.virus),
        ])], title="Virus data")

    def _build_virus(self, node):
        for name, virus_ in models.Virus.types.items():
            if node.dcs_instance() == virus_:
                break
        virus_choice = widgets.Dropdown(options=list(models.Virus.types.keys()), value=name)
        transmissibility_factor = widgets.FloatSlider(value=node.transmissibility_factor, min=0, max=1, step=0.1)
        infectious_dose = widgets.FloatText(value=node.infectious_dose, disabled=False)

        def on_virus_change(change):
            virus = models.Virus.types[change['new']]
            node.dcs_update_from(virus)
            transmissibility_factor.value = virus.transmissibility_factor
            infectious_dose.value = virus.infectious_dose
            
        def on_transmissibility_change(change):
            virus = models.SARSCoV2(viral_load_in_sputum=node.dcs_instance().viral_load_in_sputum, infectious_dose=infectious_dose.value, 
                                    viable_to_RNA_ratio=0.5, transmissibility_factor=change['new'])
            node.dcs_update_from(virus)
            if (transmissibility_factor.value != models.Virus.types[virus_choice.value].transmissibility_factor):
                virus_choice.options = list(models.Virus.types.keys()) + ["Custom"]
                virus_choice.value = "Custom"
        
        def on_infectious_dose_change(change):
            virus = models.SARSCoV2(viral_load_in_sputum=node.dcs_instance().viral_load_in_sputum, infectious_dose=change['new'], 
                                    viable_to_RNA_ratio=0.5, transmissibility_factor=transmissibility_factor.value)
            node.dcs_update_from(virus)
            if (infectious_dose.value != models.Virus.types[virus_choice.value].infectious_dose):
                virus_choice.options.append("Custom")
                virus_choice.value = "Custom"

        virus_choice.observe(on_virus_change, names=['value'])
        transmissibility_factor.observe(on_transmissibility_change, names=['value'])
        infectious_dose.observe(on_infectious_dose_change, names=['value'])

        space_between=widgets.Layout(justify_content='space-between')
        return widgets.VBox([
            widgets.HBox([widgets.Label("Virus"), virus_choice], layout=space_between), 
            widgets.HBox([widgets.Label("Tansmissibility factor "), transmissibility_factor], layout=space_between), 
            widgets.HBox([widgets.Label("Infectious dose "), infectious_dose], layout=space_between)])

    def present(self):
        return self.widget

baseline_model = models.ExposureModel(
    concentration_model=models.ConcentrationModel(
        room=models.Room(volume=75, inside_temp=models.PiecewiseConstant((0., 24.), (293.15,))),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=15),
            outside_temp=models.PiecewiseConstant((0., 24.), (283.15,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=models.InfectedPopulation(
            number=1,
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(((8., 12.), (13., 17.))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Seated'],
            expiration=models.Expiration.types['Speaking'],
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    ),
    short_range=(),
    exposed=models.Population(
        number=10,
        presence=models.SpecificInterval(((8., 12.), (13., 17.))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask'],
        host_immunity=0.,
    ),
    geographical_data=models.Cases(),
)


class CAIMIRAStateBuilder(state.StateBuilder):
    # Note: The methods in this class must correspond to the *type* of the data classes.
    # For example, build_type__VentilationBase is called when dealing with ConcentrationModel
    # types as it has a ventilation: _VentilationBase field.

    def build_type_Mask(self, _: dataclasses.Field):
        return state.DataclassStatePredefined(
            models.Mask,
            choices=models.Mask.types,
        )

    def build_type__VentilationBase(self, _: dataclasses.Field):
        s: state.DataclassStateNamed = state.DataclassStateNamed(
            states={
                'Natural': self.build_generic(models.WindowOpening),
                'No ventilation': self.build_generic(models.AirChange),
                'HVACMechanical': self.build_generic(models.HVACMechanical),
                'AirChange': self.build_generic(models.AirChange),
                'Hinged window': self.build_generic(models.WindowOpening),
                'HEPAFilter': self.build_generic(models.HEPAFilter),

            },
            state_builder=self,
        )
        #Initialise the "Hinged window" state
        s._states['Hinged window'].dcs_update_from(
            models.HingedWindow(active=models.PeriodicInterval(period=120, duration=15),
                outside_temp=models.PiecewiseConstant((0,24.), (283.15,)),
                window_height=1.6, opening_length=0.6,
                window_width=10.
            ),
        )
        # Initialise the "HVAC" state
        s._states['HVACMechanical'].dcs_update_from(
            models.HVACMechanical(active=models.PeriodicInterval(period=24*60, duration=24*60), q_air_mech=500.)
        )
        s._states['AirChange'].dcs_update_from(
            models.AirChange(models.PeriodicInterval(period=24*60, duration=24*60), 10.)
        )
        # Initialize the "No ventilation" state
        s._states['No ventilation'].dcs_update_from(
            models.AirChange(active=models.PeriodicInterval(period=60, duration=60), air_exch=0.)  #will need to add the residual air change of 0.25
        )
        s._states['HEPAFilter'].dcs_update_from(
            models.HEPAFilter(active=models.PeriodicInterval(period=60, duration=60), q_air_mech=500.)
        )
        return s


class ExpertApplication(Controller):
    def __init__(self) -> None:
        self._debug_output = widgets.Output()

        #: A list of scenario name and ModelState instances. This is intended to be
        #: mutated. Any mutation should notify the appropriate Views for handling.
        self._model_scenarios: typing.List[ScenarioType] = []
        self._active_scenario = 0
        self.multi_model_view = MultiModelView(self)
        self.comparison_view = ExposureComparissonResult()
        self.current_scenario_figure = ExposureModelResult()
        self._results_tab = widgets.Tab(children=(
            self.current_scenario_figure.widget,
            self.comparison_view.widget,
            # self._debug_output,
        ))
        self._results_tab.titles = ['Current scenario', 'Scenario comparison', "Debug"]
        self.widget = widgets.HBox(
            children=(
                self.multi_model_view.widget,
                self._results_tab,
            ),
        )
        self.add_scenario('Scenario 1')

    def build_new_model(self) -> state.DataclassInstanceState[models.ExposureModel]:
        default_model = state.DataclassInstanceState(
            models.ExposureModel,
            state_builder=CAIMIRAStateBuilder(),
        )
        default_model.dcs_update_from(baseline_model)
        # For the time-being, we have to initialise the select states. Careful
        # as values might not correspond to what the baseline model says.
        default_model.concentration_model.infected.mask.dcs_select('No mask')
        return default_model

    def add_scenario(self, name, copy_from_model: typing.Optional[state.DataclassInstanceState] = None):
        model = self.build_new_model()
        if copy_from_model is not None:
            model.dcs_update_from(copy_from_model.dcs_instance())
        self._model_scenarios.append((name, model))
        self._active_scenario = len(self._model_scenarios) - 1
        model.dcs_observe(self.notify_model_values_changed)
        self.notify_scenarios_changed()

    def _find_model_id(self, model_id):
        for index, (name, model) in enumerate(list(self._model_scenarios)):
            if id(model) == model_id:
                return index, name, model
        else:
            raise ValueError("Model not found")

    def rename_scenario(self, model_id, new_name):
        index, _, model = self._find_model_id(model_id)
        self._model_scenarios[index] = (new_name, model)
        self.notify_scenarios_changed()

    def remove_scenario(self, model_id):
        index, _, model = self._find_model_id(model_id)
        self._model_scenarios.pop(index)
        if self._active_scenario >= index:
            self._active_scenario = max(self._active_scenario - 1, 0)
        self.notify_scenarios_changed()

    def set_active_scenario(self, model_id):
        index, _, model = self._find_model_id(model_id)
        self._active_scenario = index
        self.notify_scenarios_changed()
        self.notify_model_values_changed()

    def notify_scenarios_changed(self):
        """
        Occurs when the set of scenarios has been modified, but not if the values of the scenario has changed.

        """
        self.multi_model_view.scenarios_updated(self._model_scenarios, self._active_scenario)
        self.comparison_view.scenarios_updated(self._model_scenarios, self._active_scenario)

    def notify_model_values_changed(self):
        """
        Occurs when *any* value in *any* of the scenarios has been modified.
        """
        self.comparison_view.scenarios_updated(self._model_scenarios, self._active_scenario)
        self.current_scenario_figure.update(self._model_scenarios[self._active_scenario][1].dcs_instance())


class MultiModelView(View):
    def __init__(self, controller: ExpertApplication):
        self._controller = controller
        self.widget = widgets.Tab()
        self.widget.observe(self._on_tab_change, 'selected_index')
        self._tab_model_ids: typing.List[int] = []
        self._tab_widgets: typing.List[widgets.Widget] = []
        self._tab_model_views: typing.List[ModelWidgets] = []

    def scenarios_updated(
            self,
            model_scenarios: typing.Sequence[ScenarioType],
            active_scenario_index: int
    ):
        """
        Called when a scenario is added/removed/renamed etc.

        Note: Not called when the model state is modified.

        """
        model_scenario_ids = []
        for i, (scenario_name, model) in enumerate(model_scenarios):
            if id(model) not in self._tab_model_ids:
                self.add_tab(scenario_name, model)
            model_scenario_ids.append(id(model))
            tab_index = self._tab_model_ids.index(id(model))
        self.widget.titles = [scenario_name for (scenario_name, _) in model_scenarios]

        # Any remaining model_scenario_ids are no longer needed, so remove
        # their tabs.
        for tab_index, tab_scenario_id in enumerate(self._tab_model_ids[:]):
            if tab_scenario_id not in model_scenario_ids:
                self.remove_tab(tab_index)

        assert self._tab_model_ids == model_scenario_ids

        self.widget.selected_index = active_scenario_index

    def add_tab(self, name, model):
        self._tab_model_views.append(ModelWidgets(model))
        self._tab_model_ids.append(id(model))
        tab_idx = len(self._tab_model_ids) - 1
        tab_widget = widgets.VBox(
            children=(
                self._build_settings_menu(name, model),
                self._tab_model_views[tab_idx].widget,
            )
        )
        self._tab_widgets.append(tab_widget)
        self.update_tab_widget()

    def remove_tab(self, tab_index):
        assert 0 <= tab_index < len(self._tab_model_ids)
        assert len(self._tab_model_ids) > 1
        self._tab_model_ids.pop(tab_index)
        self._tab_widgets.pop(tab_index)
        self._tab_model_views.pop(tab_index)
        if self._active_tab_index >= tab_index:
            self._active_tab_index = max(0, self._active_tab_index - 1)
        self.update_tab_widget()

    def update_tab_widget(self):
        self.widget.children = tuple(self._tab_widgets)

    def _on_tab_change(self, change):
        self._controller.set_active_scenario(
            self._tab_model_ids[change['new']]
        )

    def _build_settings_menu(self, name, model):
        delete_button = widgets.Button(description='Delete Scenario', button_style='danger')
        rename_text_field = widgets.Text(description='Rename Scenario:', value=name,
                                         style={'description_width': 'auto'})
        duplicate_button = widgets.Button(description='Duplicate Scenario', button_style='success')
        model_id = id(model)

        def on_delete_click(b):
            self._controller.remove_scenario(model_id)

        def on_rename_text_field(change):
            self._controller.rename_scenario(model_id, new_name=change['new'])

        def on_duplicate_click(b):
            tab_index = self._tab_model_ids.index(model_id)
            name = self.widget.get_title(tab_index)
            self._controller.add_scenario(f'{name} (copy)', model)

        delete_button.on_click(on_delete_click)
        duplicate_button.on_click(on_duplicate_click)
        rename_text_field.observe(on_rename_text_field, 'value')
        # TODO: This should be dynamic - we don't want to be able to delete the
        # last scenario, so this should be controlled in the remove_tab method.
        buttons_w_delete = widgets.HBox(children=(duplicate_button, delete_button))
        buttons = duplicate_button if len(self._tab_model_ids) < 2 else buttons_w_delete
        return widgets.VBox(children=(buttons, rename_text_field))


def models_start_end(models: typing.Sequence[models.ExposureModel]) -> typing.Tuple[float, float]:
    """
    Returns the earliest start and latest end time of a collection of ConcentrationModel objects

    """
    infected_start = min(model.concentration_model.infected.presence.boundaries()[0][0] for model in models)
    infected_finish = min(model.concentration_model.infected.presence.boundaries()[-1][1] for model in models)
    return infected_start, infected_finish
