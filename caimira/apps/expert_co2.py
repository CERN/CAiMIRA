import dataclasses
import ipywidgets as widgets
import typing
import numpy as np

from caimira import data, models, state
import matplotlib
import matplotlib.figure
import matplotlib.lines as mlines
import matplotlib.patches as patches
from .expert import collapsible, ipympl_canvas, WidgetGroup, CAIMIRAStateBuilder


baseline_model = models.CO2ConcentrationModel(
    room=models.Room(volume=120, humidity=0.5, inside_temp=models.PiecewiseConstant((0., 24.), (293.15,))),
    ventilation=models.HVACMechanical(active=models.PeriodicInterval(period=120, duration=120), q_air_mech=500),
    CO2_emitters=models.Population(
        number=10,
        presence=models.SpecificInterval(((8., 12.), (13., 17.))),
        mask=models.Mask.types['No mask'],
        activity=models.Activity.types['Seated'],
        host_immunity=0.,
    ),
    CO2_atmosphere_concentration=440.44,
    CO2_fraction_exhaled=0.042,
)


class Controller:
    """
    The singleton thing which is the top-level Application.

    It is responsible for owning the Model data and the Views, and
    orchestrating event messages to each if the Model/View change.

    """
    pass


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


class ExposureModelResult(View):
    def __init__(self):
        self.figure = matplotlib.figure.Figure(figsize=(9, 6))
        ipympl_canvas(self.figure)
        self.html_output = widgets.HTML()
        self.ax = self.initialize_axes()
        self.concentration_line = None
        self.concentration_area = None

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
        ax.set_ylabel('CO₂ concentration (ppm)')
        ax.set_title('CO₂ Concentration')

        return ax

    def update(self, model: models.CO2ConcentrationModel):
        self.update_plot(model)

    def update_plot(self, model: models.CO2ConcentrationModel):
        resolution = 600
        ts = np.linspace(sorted(model.CO2_emitters.presence.transition_times())[0],
                         sorted(model.CO2_emitters.presence.transition_times())[-1], resolution)
        concentration = [model.concentration(t) for t in ts]

        if self.concentration_line is None:
            [self.concentration_line] = self.ax.plot(ts, concentration, color='#3530fe')

        else:
            self.ax.ignore_existing_data_limits = False
            self.concentration_line.set_data(ts, concentration)
        
        if self.concentration_area is None:
            self.concentration_area = self.ax.fill_between(x = ts, y1=0, y2=concentration, color="#96cbff",
                where = ((model.CO2_emitters.presence.boundaries()[0][0] < ts) & (ts < model.CO2_emitters.presence.boundaries()[0][1]) | 
                    (model.CO2_emitters.presence.boundaries()[1][0] < ts) & (ts < model.CO2_emitters.presence.boundaries()[1][1])))
                   
        else:
            self.concentration_area.remove()         
            self.concentration_area = self.ax.fill_between(x = ts, y1=0, y2=concentration, color="#96cbff",
                where = ((model.CO2_emitters.presence.boundaries()[0][0] < ts) & (ts < model.CO2_emitters.presence.boundaries()[0][1]) | 
                    (model.CO2_emitters.presence.boundaries()[1][0] < ts) & (ts < model.CO2_emitters.presence.boundaries()[1][1])))

        concentration_top = max(np.array(concentration))
        self.ax.set_ylim(bottom=model.CO2_atmosphere_concentration * 0.9, top=concentration_top*1.1)
        self.ax.set_xlim(left = min(model.CO2_emitters.presence.boundaries()[0])*0.95, 
                        right = max(model.CO2_emitters.presence.boundaries()[1])*1.05)
   
        figure_legends = [mlines.Line2D([], [], color='#3530fe', markersize=15, label='CO₂ concentration'),
                mlines.Line2D([], [], color='salmon', markersize=15, label='Insufficient level', linestyle='--'),
                mlines.Line2D([], [], color='limegreen', markersize=15, label='Acceptable level', linestyle='--'),
                patches.Patch(edgecolor="#96cbff", facecolor='#96cbff', label='Presence of person(s)')]
        self.ax.legend(handles=figure_legends)
        if 1500 < concentration_top:
            self.ax.set_ylim(top=concentration_top*1.1)
        else:
            self.ax.set_ylim(top=1550)
        self.ax.hlines([800, 1500], xmin=min(model.CO2_emitters.presence.boundaries()[0])*0.95, xmax=max(model.CO2_emitters.presence.boundaries()[1])*1.05, colors=['limegreen', 'salmon'], linestyles='dashed') 
        self.figure.canvas.draw()


class ExposureComparisonResult(View):
    def __init__(self):
        self.figure = matplotlib.figure.Figure(figsize=(9, 6))
        ipympl_canvas(self.figure)
        self.html_output = widgets.HTML()
        self.ax = self.initialize_axes()

    @property
    def widget(self):
        # Workaround to a bug with ipymlp, which doesn't work well with tabs
        # unless the widget is wrapped in a container (it is seen on all tabs otherwise!).
        return widgets.HBox([self.figure.canvas])

    def initialize_axes(self) -> matplotlib.figure.Axes:
        ax = self.figure.add_subplot(1, 1, 1)
        ax.spines[['right', 'top']].set_visible(False)
        
        ax.set_xlabel('Time (hours)')
        ax.set_ylabel('CO₂ concentration (ppm)')
        ax.set_title('CO₂ Concentration')

        return ax

    def scenarios_updated(self, scenarios: typing.Sequence[ScenarioType], _):
        updated_labels, updated_models = zip(*scenarios)
        CO2_models = tuple(
            model.dcs_instance() for model in updated_models
        )
        self.update_plot(CO2_models, updated_labels)

    def update_plot(self, CO2_models: typing.Tuple[models.CO2ConcentrationModel, ...], labels: typing.Tuple[str, ...]):
        self.ax.cla()

        start, finish = models_start_end(CO2_models)
        colors=['blue', 'red', 'orange', 'yellow', 'pink', 'purple', 'green', 'brown', 'black' ]
        ts = np.linspace(start, finish, num=250)

        concentrations = [[conc_model.concentration(t) for t in ts] for conc_model in CO2_models]
        for label, concentration, color in zip(labels, concentrations, colors):
            self.ax.plot(ts, concentration, label=label, color=color)
            
        concentration_top = max([max(np.array(concentration)) for concentration in concentrations])
        concentration_min = min([model.CO2_atmosphere_concentration for model in CO2_models])
        
        self.ax.set_ylim(bottom=concentration_min * 0.9, top=concentration_top*1.1)
        self.ax.set_xlim(left = start*0.95, 
                        right = finish*1.05)
        if 1500 < concentration_top:
            self.ax.set_ylim(top=concentration_top*1.1)
        else:
            self.ax.set_ylim(top=1550)
        self.ax.hlines([800, 1500], xmin=start*0.95, xmax=finish*1.05, colors=['limegreen', 'salmon'], linestyles='dashed') 

        self.ax.legend()
        self.figure.canvas.draw_idle()
        self.figure.canvas.flush_events()


class CO2Application(Controller):
    def __init__(self) -> None:
        # self._debug_output = widgets.Output()

        #: A list of scenario name and ModelState instances. This is intended to be
        #: mutated. Any mutation should notify the appropriate Views for handling.
        self._model_scenarios: typing.List[ScenarioType] = []
        self._active_scenario = 0
        self.multi_model_view = MultiModelView(self)
        self.comparison_view = ExposureComparisonResult()
        self.current_scenario_figure = ExposureModelResult()
        self._results_tab = widgets.Tab(children=(
            self.current_scenario_figure.widget,
            self.comparison_view.widget,
            # self._debug_output,
        ))
        for i, title in enumerate(['Current scenario', 'Scenario comparison', "Debug"]):
            self._results_tab.set_title(i, title)

        self.widget = widgets.HBox(
            children=(
                self.multi_model_view.widget,
                self._results_tab,
            ),
        )
        self.add_scenario('Scenario 1')

    def build_new_model(self, vent: str) -> state.DataclassInstanceState[models.CO2ConcentrationModel]:
        new_model = state.DataclassInstanceState(
            models.CO2ConcentrationModel,
            state_builder=CAIMIRACO2StateBuilder(selected_ventilation=vent)
        )
        return new_model

    def add_scenario(self, name, copy_from_model: typing.Optional[state.DataclassInstanceState] = None):
        if copy_from_model is not None:
            model = self.build_new_model(vent=copy_from_model.ventilation._selected)
            model.dcs_update_from(copy_from_model.dcs_instance())
        else:
            model = self.build_new_model(vent='HVACMechanical') # Default
            model.dcs_update_from(baseline_model)
            
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
        self.multi_model_view.remove_tab(index)
        self._active_scenario = index - 1

        model.dcs_observe(self.notify_model_values_changed)
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


class ModelWidgets(View):
    def __init__(self, model_state: state.DataclassState):
        #: The widgets that this view produces (inputs and outputs together)
        self.widget = widgets.VBox([])
        self.construct_widgets(model_state)

    def construct_widgets(self, model_state: state.DataclassState):
        # Build the input widgets.
        self._build_widget(model_state)

    def _build_widget(self, node):
        self.widget.children += (self._build_room(node.room),)
        self.widget.children += (self._build_population(node.CO2_emitters, node.ventilation),)
        self.widget.children += (self._build_atmospheric_concentration(node),)
        self.widget.children += (self._build_ventilation(node.ventilation, node.CO2_emitters),)

    def _build_atmospheric_concentration(self, node):
        return collapsible([widgets.VBox([
            self._build_co2_concentration(node),
        ])], title="Carbon Dioxide")
        
    def _build_population(self, node, ventilation_node):
        return collapsible([widgets.VBox([
            self._build_population_number(node),
            self._build_activity(node.activity),
            self._build_population_presence(node.presence, ventilation_node)
        ])], title="Population")
    
    def _build_co2_concentration(self, node):
        concentration = widgets.IntSlider(value=node.CO2_atmosphere_concentration, min=300, max=1000, step=10)

        def on_atmospheric_concentration_change(change):
            node.CO2_atmosphere_concentration = change['new']
        
        concentration.observe(on_atmospheric_concentration_change, names=['value'])

        return widgets.HBox([widgets.Label('Atmospheric Concentration (ppm) '), concentration], layout=widgets.Layout(justify_content='space-between'))

    def _build_room(self,node):
        room_volume = widgets.IntSlider(value=node.volume, min=5, max=200, step=5)
        humidity = widgets.FloatSlider(value = node.humidity*100, min=20, max=80, step=5)
        inside_temp = widgets.IntSlider(value=node.inside_temp.values[0]-273.15, min=15., max=25.)

        def on_volume_change(change):
            node.volume = change['new'] 

        def on_humidity_change(change):
            node.humidity = change['new']/100

        def on_insidetemp_change(change):
            node.inside_temp.values = (change['new']+273.15,)

        room_volume.observe(on_volume_change, names=['value'])
        humidity.observe(on_humidity_change, names=['value'])
        inside_temp.observe(on_insidetemp_change, names=['value'])

        widget = collapsible(
            [ widgets.VBox([
                widgets.HBox([widgets.Label('Room volume (m³)'), room_volume],
                layout=widgets.Layout(width='100%', justify_content='space-between')),
                widgets.HBox([widgets.Label('Inside temperature (℃)'), inside_temp],
                layout=widgets.Layout(width='100%', justify_content='space-between')),
                widgets.HBox([widgets.Label('Indoor relative humidity (%)'), humidity],
                layout=widgets.Layout(width='100%', justify_content='space-between')),])
            ], title="Specification of workspace"
        )

        return widget

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

    def _build_population_number(self, node):
        number = widgets.IntSlider(value=node.number, min=1, max=200, step=1)

        def on_population_number_change(change):
            node.number = change['new']
        
        number.observe(on_population_number_change, names=['value'])

        return widgets.HBox([widgets.Label('Number of people in the room '), number], layout=widgets.Layout(justify_content='space-between'))

    def _build_population_presence(self, node, ventilation_node):
        presence_start = widgets.FloatRangeSlider(value = node.present_times[0], min = 8., max=13., step=0.1)
        presence_finish = widgets.FloatRangeSlider(value = node.present_times[1], min = 13., max=18., step=0.1)

        def on_presence_start_change(change):
            ventilation_node.active.start = change['new'][0] - ventilation_node.active.duration / 60
            node.present_times = (change['new'], presence_finish.value)

        def on_presence_finish_change(change):
            node.present_times = (presence_start.value, change['new'])
        
        presence_start.observe(on_presence_start_change, names=['value'])
        presence_finish.observe(on_presence_finish_change, names=['value'])

        return widgets.HBox([widgets.Label('Population presence'),  presence_start, presence_finish], layout = widgets.Layout(justify_content='space-between'))

    def present(self):
        return self.widget

    def _build_ventilation(
            self,
            node: typing.Union[
                state.DataclassStateNamed[models.Ventilation],
                state.DataclassStateNamed[models.MultipleVentilation],
            ],
            emitters_node: models.Population,
    ) -> widgets.Widget:
        ventilation_widgets = {
            'HVACMechanical': self._build_mechanical(node),
            'Sliding window': self._build_window(node, emitters_node),
            'No ventilation': self._build_no_ventilation(node._states['No ventilation']),
        }

        keys=[("Mechanical", "HVACMechanical"), ("Natural", "Sliding window"), ("No ventilation", "No ventilation")]

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

            hinged_window.observe(on_hinged_window_change, names=['value'])
            
            return widgets.HBox([widgets.Label('Window width (meters) '), hinged_window], layout=widgets.Layout(justify_content='space-between', width='100%'))

    def _build_sliding_window(self, node):
        return widgets.HBox([]) 

    def _build_window(self, node, emitters_node) -> WidgetGroup:
        window_widgets = {
            'Sliding window': self._build_sliding_window(node._states['Sliding window']),
            'Hinged window': self._build_hinged_window(node._states['Hinged window']), 
        }

        for name, widget in window_widgets.items():
            widget.layout.visible = False
            widget.layout.display = 'none'

        window_w = widgets.RadioButtons(
            options= list(zip(['Sliding window', 'Hinged window'], window_widgets.keys())),
            button_style='info',
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

        number_of_windows= widgets.IntText(value= 1, min= 0, max= 5, step=1)
        frequency = widgets.IntSlider(value=node.active.period, min=0, max=120)
        duration = widgets.IntSlider(value=node.active.duration, min=0, max=frequency.value)
        opening_length = widgets.FloatSlider(value=node.opening_length, min=0, max=3, step=0.1)
        window_height = widgets.FloatSlider(value=node.window_height, min=0, max=3, step=0.1)

        def on_value_change(change):
            node.number_of_windows = change['new']
        
        def on_period_change(change):
            node.active.period = change['new']
            duration.max = change['new']

        def on_duration_change(change):
            node.active.start = emitters_node.presence.present_times[0][0] - change['new'] / 60
            node.active.duration = change['new']

        def on_opening_length_change(change):
            node.opening_length = change['new']
        
        def on_window_height_change(change):
            node.window_height = change['new']

        number_of_windows.observe(on_value_change, names=['value'])
        frequency.observe(on_period_change, names=['value'])
        duration.observe(on_duration_change, names=['value'])
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
                    widgets.Label('Frequency (minutes)', layout=auto_width),
                    frequency,
                ),
                (
                    widgets.Label('Duration (minutes)', layout=auto_width),
                    duration,
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

        q_air_mech.observe(on_q_air_mech_change, names=['value'])

        return widgets.HBox([q_air_mech, widgets.Label('m³/h')])

    def _build_ach(self, node):
        air_exch = widgets.IntSlider(value=node.air_exch, min=0, max=20, step=1)

        def on_air_exch_change(change):
            node.air_exch = change['new']

        air_exch.observe(on_air_exch_change, names=['value'])

        return widgets.HBox([air_exch, widgets.Label('h⁻¹')])

    def _build_mechanical(self, node):
        mechanical_widgets = {
            'HVACMechanical': self._build_q_air_mech(node._states['HVACMechanical']),
            'AirChange': self._build_ach(node._states['AirChange']),
        }

        for name, widget in mechanical_widgets.items():
            widget.layout.visible = False

        mechanical_w = widgets.RadioButtons(
            options=list(zip(['Air supply flow rate (m³/h)', 'Air changes per hour (h⁻¹)'], mechanical_widgets.keys())),
            button_style='info',
        )

        def toggle_mechanical(value):
            for name, widget in mechanical_widgets.items():
                widget.layout.visible = False
                widget.layout.display = 'none'

            node.dcs_select(value)
            widget = mechanical_widgets[value]
            widget.layout.visible = True
            widget.layout.display = 'flex'

        mechanical_w.observe(lambda event: toggle_mechanical(event['new']), 'value')
        toggle_mechanical(mechanical_w.value)

        return widgets.VBox([mechanical_w, widgets.HBox(list(mechanical_widgets.values()))])

    def _build_no_ventilation(self, node):
        return widgets.HBox([])

    
class MultiModelView(View):
    def __init__(self, controller: CO2Application):
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
            self.widget.set_title(tab_index, scenario_name)

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
        duplicate_button = widgets.Button(description='Replicate Scenario', button_style='success')
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
        
        buttons_w_delete = widgets.HBox(children=(duplicate_button, delete_button))
        buttons = duplicate_button if len(self._tab_model_ids) < 2 else buttons_w_delete
        
        return widgets.VBox(children=(buttons, rename_text_field))
    

class CAIMIRACO2StateBuilder(CAIMIRAStateBuilder):
    
    def __init__(self, selected_ventilation: str):
        self.selected_ventilation = selected_ventilation

    def build_type__VentilationBase(self, _: dataclasses.Field):
        s: state.DataclassStateNamed = state.DataclassStateNamed(
            states={
                'HVACMechanical': self.build_generic(models.HVACMechanical),
                'Sliding window': self.build_generic(models.WindowOpening),
                'No ventilation': self.build_generic(models.AirChange),
                'AirChange': self.build_generic(models.AirChange),
                'Hinged window': self.build_generic(models.WindowOpening),
            },
            base_type=self.selected_ventilation,
            state_builder=self,
        )
        s._states['HVACMechanical'].dcs_update_from(baseline_model.ventilation)
        #Initialise the "Sliding window" state
        s._states['Sliding window'].dcs_update_from(
            models.SlidingWindow(active=models.PeriodicInterval(period=120, duration=15, start=8-(15/60)),
                outside_temp=models.PiecewiseConstant((0,24.), (283.15,)),
                window_height=1.6, opening_length=0.6,
                ),
        )
        #Initialise the "Hinged window" state
        s._states['Hinged window'].dcs_update_from(
            models.HingedWindow(active=models.PeriodicInterval(period=120, duration=15, start=8-(15/60)),
                outside_temp=models.PiecewiseConstant((0,24.), (283.15,)),
                window_height=1.6, opening_length=0.6,
                window_width=10.
            ),
        )
        s._states['AirChange'].dcs_update_from(
            models.AirChange(models.PeriodicInterval(period=24*60, duration=24*60), 10.)
        )
        # Initialize the "No ventilation" state
        s._states['No ventilation'].dcs_update_from(
            models.AirChange(active=models.PeriodicInterval(period=60, duration=60), air_exch=0.) 
        )
        return s

def models_start_end(models: typing.Sequence[models.CO2ConcentrationModel]) -> typing.Tuple[float, float]:
    """
    Returns the earliest start and latest end time of a collection of v objects

    """
    emitters_start = min(model.CO2_emitters.presence.boundaries()[0][0] for model in models)
    emitters_finish = min(model.CO2_emitters.presence.boundaries()[-1][1] for model in models)
    return emitters_start, emitters_finish
