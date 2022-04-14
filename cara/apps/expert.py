import dataclasses
import typing
import uuid

import ipympl.backend_nbagg
import ipywidgets as widgets
import matplotlib
import matplotlib.figure
import numpy as np
from numpy import object_
from cara import data, models, state


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
        self.ax = self.figure.add_subplot(1, 1, 1)
        self.line = None

    @property
    def widget(self):
        return widgets.VBox([
            self.html_output,
            self.figure.canvas,
        ])

    def update(self, model: models.ExposureModel):
        self.update_plot(model.concentration_model)
        self.update_textual_result(model)

    def update_plot(self, model: models.ConcentrationModel):
        resolution = 600
        ts = np.linspace(sorted(model.infected.presence.transition_times())[0],
                         sorted(model.infected.presence.transition_times())[-1], resolution)
        concentration = [model.concentration(t) for t in ts]
        if self.line is None:
            [self.line] = self.ax.plot(ts, concentration)
            ax = self.ax

            # ax.text(0.5, 0.9, 'Without masks & window open', transform=ax.transAxes, ha='center')

            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)

            ax.set_xlabel('Time (hours)')
            ax.set_ylabel('Concentration ($virions/m^{3}$)')
            ax.set_title('Concentration of virions')
        else:
            self.ax.ignore_existing_data_limits = True
            self.line.set_data(ts, concentration)
        # Update the top limit based on the concentration if it exceeds 5
        # (rare but possible).
        top = max([3, max(concentration)])
        self.ax.set_ylim(bottom=0., top=top)
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
        self.ax = self.initialize_axes()

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
        ax.set_ylabel('Concentration ($virions/m^{3}$)')
        ax.set_title('Concentration of virions')
        return ax

    def scenarios_updated(self, scenarios: typing.Sequence[ScenarioType], _):
        updated_labels, updated_models = zip(*scenarios)
        conc_models = tuple(
            model.concentration_model.dcs_instance() for model in updated_models
        )
        self.update_plot(conc_models, updated_labels)

    def update_plot(self, conc_models: typing.Tuple[models.ConcentrationModel, ...], labels: typing.Tuple[str, ...]):
        self.ax.lines.clear()
        start, finish = models_start_end(conc_models)
        ts = np.linspace(start, finish, num=250)
        concentrations = [[conc_model.concentration(t) for t in ts] for conc_model in conc_models]
        for label, concentration in zip(labels, concentrations):
            self.ax.plot(ts, concentration, label=label)

        top = max(3., max([max(conc) for conc in concentrations]))
        self.ax.set_ylim(bottom=0., top=top)

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
        self.widget.children += (self._build_infected(node.concentration_model.infected),)
        self.widget.children += (self._build_exposed(node),)
        self.widget.children += (self._build_infectivity(node.concentration_model.infected),)

    def _build_exposed(self, node):
        return collapsible([widgets.VBox([
            self._build_exposed_number(node.exposed),
            self._build_mask(node.exposed.mask),
            self._build_activity(node.exposed.activity),
        ])], title="Exposed")

    def _build_infected(self, node):
        return collapsible([widgets.VBox([
            self._build_infected_number(node),
            self._build_mask(node.mask),
            self._build_activity(node.activity),
            self._build_expiration(node.expiration),
        ])], title="Infected")

    def _build_room_volume(self, node):
        room_volume = widgets.FloatSlider(value=node.volume, min=10, max=500
        , step=5)

        def on_value_change(change):
            node.volume = change['new']

        # TODO: Link the state back to the widget, not just the other way around.
        room_volume.observe(on_value_change, names=['value'])
    
        return widgets.HBox([widgets.Label('Room volume (m³)'), room_volume], layout=widgets.Layout(justify_content='space-between'))


    def _build_room_area(self, node):
        room_surface = widgets.FloatSlider(value=25, min=1, max=200, step=10)
        room_ceiling_height = widgets.FloatSlider(value=3, min=1, max=20, step=1)
        displayed_volume=widgets.Label('1')

        def room_surface_change(change):
            node.volume = change['new']*room_ceiling_height.value 
            displayed_volume.value=str(node.volume)

        def room_ceiling_height_change(change):
            node.volume = change['new']*room_surface.value 
            displayed_volume.value=str(node.volume)

        room_surface.observe(room_surface_change, names=['value'])
        room_ceiling_height.observe(room_ceiling_height_change, names=['value'])        

        return widgets.VBox([widgets.HBox([widgets.Label('Room surface area (m²) '), room_surface]
        , layout=widgets.Layout(justify_content='space-between', width='100%'))
        , widgets.HBox([widgets.Label('Room ceiling height (m)'), room_ceiling_height]
        , layout=widgets.Layout(justify_content='space-between', width='100%'))
        , widgets.HBox([widgets.Label('Total volume :'), displayed_volume, widgets.Label('m³')])])

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
            button_style='info',
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

        humidity = widgets.FloatSlider(value = node.humidity, min=0, max=1, step=0.01)

        def humidity_change(change):
            node.humidity = change['new']

        humidity.observe(humidity_change, names=['value'])

        widget = collapsible(
            [ widgets.VBox([
                widgets.HBox([
                    widgets.Label('Room number '), room_number]
                    , layout=widgets.Layout(width='100%', justify_content='space-between'))
            , room_w, widgets.VBox(list(room_widgets.values()))
            , widgets.HBox([widgets.Label('Relative humidity rate in the room depending on the use of a central heating system'),humidity]
            , layout=widgets.Layout(width='100%', justify_content='space-between'))
            ])]
            , title="Specification of workspace"
        )

        return widget

    def _build_outsidetemp(self, node) -> WidgetGroup:
        outside_temp = widgets.IntSlider(value=10, min=-10, max=30)

        def outsidetemp_change(change):
            node.values = (change['new'] + 273.15, )

        outside_temp.observe(outsidetemp_change, names=['value'])
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

            def hinged_window_change(change):
                node.window_width = change['new']

            # TODO: Link the state back to the widget, not just the other way around.
            hinged_window.observe(hinged_window_change, names=['value'])
            
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

        number_of_windows= widgets.IntSlider(value= 1, min= 0, max= 5, step=1)
        period = widgets.IntSlider(value=node.active.period, min=0, max=240)
        interval = widgets.IntSlider(value=node.active.duration, min=0, max=240)
        inside_temp = widgets.IntSlider(value=node.inside_temp.values[0]-273.15, min=15., max=25.)
        opening_length = widgets.FloatSlider(value=node.opening_length, min=0, max=3, step=0.1)
        window_height = widgets.FloatSlider(value=node.window_height, min=0, max=3, step=0.1)

        def on_value_change(change):
            node.number_of_windows = change['new']
        
        def on_period_change(change):
            node.active.period = change['new']

        def on_interval_change(change):
            node.active.duration = change['new']

        def insidetemp_change(change):
            node.inside_temp.values = (change['new']+273.15,)

        def opening_length_change(change):
            node.opening_length = change['new']
        
        def window_height_change(change):
            node.window_height = change['new']

        # TODO: Link the state back to the widget, not just the other way around.
        number_of_windows.observe(on_value_change, names=['value'])
        period.observe(on_period_change, names=['value'])
        interval.observe(on_interval_change, names=['value'])
        inside_temp.observe(insidetemp_change, names=['value'])
        opening_length.observe(opening_length_change, names=['value'])
        window_height.observe(window_height_change, names=['value'])

        outsidetemp_widgets = {
            'Fixed': self._build_outsidetemp(node.outside_temp),
            'Daily variation': self._build_month(node),
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
                    widgets.Label('Inside temperature (℃)', layout=auto_width),
                    inside_temp,
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
        q_air_mech = widgets.FloatSlider(value=node.q_air_mech, min=0, max=1000, step=5)

        def q_air_mech_change(change):
            node.q_air_mech = change['new']

        # TODO: Link the state back to the widget, not just the other way around.
        q_air_mech.observe(q_air_mech_change, names=['value'])

        return widgets.HBox([q_air_mech, widgets.Label('m³/h')])

    def _build_ach(self, node):
        air_exch = widgets.IntSlider(value=node.air_exch, min=0, max=50, step=5)

        def air_exch_change(change):
            node.air_exch = change['new']

        # TODO: Link the state back to the widget, not just the other way around.
        air_exch.observe(air_exch_change, names=['value'])

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

        def exposed_number_change(change):
            node.number = change['new']
        # TODO: Link the state back to the widget, not just the other way around.
        number.observe(exposed_number_change, names=['value'])

        return widgets.HBox([widgets.Label('Number of exposed people in the room '), number], layout=widgets.Layout(justify_content='space-between'))

    def _build_infected_number(self, node):
        number = widgets.IntSlider(value=node.number, min=1, max=200, step=1)

        def infected_number_change(change):
            node.number = change['new']
        # TODO: Link the state back to the widget, not just the other way around.
        number.observe(infected_number_change, names=['value'])

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

    def _build_infectivity(self,node):
        return collapsible([widgets.VBox([
            self._build_virus(node.virus),
        ])], title="Virus variant")

    def _build_virus(self, node):
        virus = node.dcs_instance()
        for name, virus_ in models.Virus.types.items():
            if virus == virus_:
                break
        virus_choice = widgets.Dropdown(options=list(models.Virus.types.keys()), value=name)

        def on_virus_change(change):
            node.dcs_select(change['new'])
        virus_choice.observe(on_virus_change, names=['value'])

        return widgets.HBox([widgets.Label("Virus"), virus_choice], layout=widgets.Layout(justify_content='space-between'))


    def present(self):
        return self.widget


baseline_model = models.ExposureModel(
    concentration_model=models.ConcentrationModel(
        room=models.Room(volume=75, humidity=0.5),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period= 120, duration= 15),
            inside_temp=models.PiecewiseConstant((0., 24.), (293.15,)),
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
)


class CARAStateBuilder(state.StateBuilder):
    # Note: The methods in this class must correspond to the *type* of the data classes.
    # For example, build_type__VentilationBase is called when dealing with ConcentrationModel
    # types as it has a ventilation: _VentilationBase field.

    def build_type_Mask(self, _: dataclasses.Field):
        return state.DataclassStatePredefined(
            models.Mask,
            choices=models.Mask.types,
        )

    def build_type_Virus(self, _: dataclasses.Field):
        return state.DataclassStatePredefined(
            models.Virus,
            choices=models.Virus.types,
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
            inside_temp=models.PiecewiseConstant((0,24.), (293.15,)),
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
    def __init__(self):
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
        for i, title in enumerate(['Current scenario', 'Scenario comparison', "Debug"]):
            self._results_tab.set_title(i, title)
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
            state_builder=CARAStateBuilder(),
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


def models_start_end(models: typing.Sequence[models.ConcentrationModel]) -> typing.Tuple[float, float]:
    """
    Returns the earliest start and latest end time of a collection of ConcentrationModel objects

    """
    infected_start = min(model.infected.presence.boundaries()[0][0] for model in models)
    infected_finish = min(model.infected.presence.boundaries()[-1][1] for model in models)
    return infected_start, infected_finish
