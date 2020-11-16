import dataclasses
import typing
import uuid

import ipympl.backend_nbagg
import ipywidgets as widgets
import numpy as np
import matplotlib
import matplotlib.figure

from cara import models
from cara import state
from cara import data


def collapsible(widgets_to_collapse: typing.List, title: str, start_collapsed=True):
    collapsed = widgets.Accordion([widgets.VBox(widgets_to_collapse)])
    collapsed.set_title(0, title)
    if start_collapsed:
        collapsed.selected_index = None
    return collapsed


def widget_group(label_widget_pairs):
    labels, widgets_ = zip(*label_widget_pairs)
    labels_w = widgets.VBox(labels)
    widgets_w = widgets.VBox(widgets_)
    return widgets.HBox([labels_w, widgets_w])


class ConcentrationFigure:
    def __init__(self):
        self.figure = matplotlib.figure.Figure(figsize=(9, 6))
        self.ax = self.figure.add_subplot(1, 1, 1)
        self.line = None

    def update(self, model: models.ConcentrationModel):
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
            ax.set_ylabel('Concentration ($q/m^3$)')
            ax.set_title('Concentration of infectious quanta aerosols')
        else:
            self.ax.ignore_existing_data_limits = True
            self.line.set_data(ts, concentration)
        # Update the top limit based on the concentration if it exceeds 5
        # (rare but possible).
        top = max([3, max(concentration)])
        self.ax.set_ylim(bottom=0., top=top)
        self.figure.canvas.draw()


def ipympl_canvas(figure: matplotlib.figure.Figure):
    # Make a plain matplotlib figure render as a Jupyter widget.
    matplotlib.interactive(False)
    ipympl.backend_nbagg.new_figure_manager_given_figure(uuid.uuid1(), figure)
    figure.canvas.toolbar_visible = True
    figure.canvas.toolbar.collapsed = True
    figure.canvas.footer_visible = False
    figure.canvas.header_visible = False


class WidgetView:
    def __init__(self, model_state: state.DataclassState):
        self.model_state = model_state
        self.model_state.dcs_observe(self.update)
        #: The widgets that this view produces (inputs and outputs together)
        self.widget = widgets.VBox([])
        self.widgets = {}
        self.out = widgets.Output()
        self.plots = []
        self.construct_widgets()
        # Trigger the first result.
        self.update()

    def construct_widgets(self):
        # Build the input widgets.
        self._build_widget(self.model_state)

        # And the output widget figure.
        concentration = ConcentrationFigure()
        self.plots.append(concentration)
        ipympl_canvas(concentration.figure)

        self.widgets['results'] = collapsible([
            widgets.HBox([
                concentration.figure.canvas,
                self.out,
            ])
        ], 'Results', start_collapsed=False)

        # Join inputs and outputs together in a single widget for convenience.
        self.widget.children += (self.widgets['results'], )

    def prepare_output(self):
        pass

    def update(self):
        model: models.ExposureModel = self.model_state.dcs_instance()
        for plot in self.plots:
            plot.update(model.concentration_model)

        self.out.clear_output()
        with self.out:
            P = model.infection_probability()
            print(f'Emission rate (quanta/hr): {model.concentration_model.infected.emission_rate_when_present()}')
            print(f'Probability of infection: {np.round(P, 0)}%')

            print(f'Number of exposed: {model.exposed.number}')

            new_cases = np.round(model.expected_new_cases(), 1)
            print(f'Number of expected new cases: {new_cases}')

            R0 = np.round(model.reproduction_number(), 1)
            print(f'Reproduction number (R0): {R0}')

    def _build_widget(self, node):
        self.widget.children += (self._build_room(node.concentration_model.room),)
        self.widget.children += (self._build_ventilation(node.concentration_model.ventilation),)
        self.widget.children += (self._build_infected(node.concentration_model.infected),)
        self.widget.children += (self._build_exposed(node),)

    def _build_exposed(self, node):
        return collapsible([widgets.HBox([
            self._build_mask(node.exposed.mask),
            self._build_activity(node.exposed.activity),
        ])], title="Exposed")

    def _build_infected(self, node):
        return collapsible([widgets.HBox([
            self._build_mask(node.mask),
            self._build_activity(node.activity),
            self._build_expiration(node.expiration),
        ])], title="Infected")

    def _build_room(self, node):
        room_volume = widgets.IntSlider(value=node.volume, min=10, max=150)

        def on_value_change(change):
            node.volume = change['new']

        # TODO: Link the state back to the widget, not just the other way around.
        room_volume.observe(on_value_change, names=['value'])
        def on_state_change():
            room_volume.value = node.volume
        node.dcs_observe(on_state_change)

        widget = collapsible(
            [widget_group(
                [[widgets.Label('Room volume'), room_volume]]
            )],
            title='Specification of workplace', start_collapsed=False,
        )
        return widget

    def _build_outsidetemp(self,node):
        outside_temp = widgets.IntSlider(value=10., min=-10., max=30.)

        def outsidetemp_change(change):
            node.values = (change['new']+273.15,)
        outside_temp.observe(outsidetemp_change, names=['value'])
        return widgets.VBox([
                        widgets.HBox([widgets.Label('Outside temperature',
                        layout=widgets.Layout(width='150px')), outside_temp]),
                        ])

    def _build_window(self, node):
        period = widgets.IntSlider(value=node.active.period, min=0, max=240)
        interval = widgets.IntSlider(value=node.active.duration, min=0, max=240)
        inside_temp = widgets.IntSlider(value=node.inside_temp.values[0]-273.15, min=15., max=25.)

        def on_period_change(change):
            node.active.period = change['new']

        def on_interval_change(change):
            node.active.duration = change['new']

        def insidetemp_change(change):
            node.inside_temp.values = (change['new']+273.15,)

        # TODO: Link the state back to the widget, not just the other way around.
        period.observe(on_period_change, names=['value'])
        interval.observe(on_interval_change, names=['value'])
        inside_temp.observe(insidetemp_change, names=['value'])

        outsidetemp_widgets = {
            'Fixed': self._build_outsidetemp(node.outside_temp),
            'Daily variation': self._build_month(node),
        }
        for name, widget in outsidetemp_widgets.items():
            widget.layout.visible = False

        outsidetemp_w = widgets.ToggleButtons(
            options=outsidetemp_widgets.keys(),
        )

        def toggle_outsidetemp(value):
            for name, widget in outsidetemp_widgets.items():
                widget.layout.display = 'none'

            #node.dcs_select(value)

            widget = outsidetemp_widgets[value]
            widget.layout.visible = True
            widget.layout.display = 'block'

        outsidetemp_w.observe(lambda event: toggle_outsidetemp(event['new']), 'value')
        toggle_outsidetemp(outsidetemp_w.value)

        return widgets.VBox(
                [
                    widgets.HBox([widgets.Label('Open every n minutes',
                                    layout=widgets.Layout(width='150px')), period]),
                    widgets.HBox([widgets.Label('For how long',
                                    layout=widgets.Layout(width='150px')), interval]),
                    widgets.HBox([widgets.Label('Inside temperature',
                                    layout=widgets.Layout(width='150px')), inside_temp]),
                    widget_group([[widgets.Label('Outside temp.'), outsidetemp_w]])
                 ] + list(outsidetemp_widgets.values())
            )

    def _build_mechanical(self, node):
        period = widgets.IntSlider(value=node.active.period, min=0, max=240, step=5)
        interval = widgets.IntSlider(value=node.active.duration, min=0, max=240, step=5)
        q_air_mech = widgets.IntSlider(value=node.q_air_mech, min=0, max=1000, step=5)

        def on_period_change(change):
            node.active.period = change['new']

        def on_interval_change(change):
            node.active.duration = change['new']

        def q_air_mech_change(change):
            node.q_air_mech = change['new']

        # TODO: Link the state back to the widget, not just the other way around.
        period.observe(on_period_change, names=['value'])
        interval.observe(on_interval_change, names=['value'])
        q_air_mech.observe(q_air_mech_change, names=['value'])

        return widgets.VBox(
                [
                    widgets.HBox([widgets.Label('On every n minutes',
                                    layout=widgets.Layout(width='150px')), period]),
                    widgets.HBox([widgets.Label('For how long',
                                    layout=widgets.Layout(width='150px')), interval]),
                    widgets.HBox([widgets.Label('Flow rate (m^3/h)',
                                    layout=widgets.Layout(width='150px')), q_air_mech]),
                 ]
            )

    def _build_month(self, node):

        month_choice = widgets.Select(options=list(data.GenevaTemperatures.keys()), value='Jan')

        def on_month_change(change):
            node.outside_temp = data.GenevaTemperatures[change['new']]
        month_choice.observe(on_month_change, names=['value'])

        return widget_group(
            [[widgets.Label("Month"), month_choice]]
        )

    def _build_activity(self, node):
        activity = node.dcs_instance()
        for name, activity_ in models.Activity.types.items():
            if activity == activity_:
                break
        activity = widgets.Select(options=list(models.Activity.types.keys()), value=name)

        def on_activity_change(change):
            act = models.Activity.types[change['new']]
            node.dcs_update_from(act)
        activity.observe(on_activity_change, names=['value'])

        return widget_group(
            [[widgets.Label("Activity"), activity]]
        )

    def _build_mask(self, node):
        mask = node.dcs_instance()
        for name, mask_ in models.Mask.types.items():
            if mask == mask_:
                break
        mask_choice = widgets.Select(options=list(models.Mask.types.keys()), value=name)

        def on_mask_change(change):
            node.dcs_select(change['new'])
        mask_choice.observe(on_mask_change, names=['value'])

        return widget_group(
            [[widgets.Label("Mask"), mask_choice]]
        )

    def _build_expiration(self, node):
        expiration = node.dcs_instance()
        for name, expiration_ in models.Expiration.types.items():
            if expiration == expiration_:
                break
        expiration_choice = widgets.Select(options=list(models.Expiration.types.keys()), value=name)

        def on_expiration_change(change):
            expiration = models.Expiration.types[change['new']]
            node.dcs_update_from(expiration)
        expiration_choice.observe(on_expiration_change, names=['value'])

        return widget_group(
            [[widgets.Label("Expiration"), expiration_choice]]
        )

    def _build_ventilation(self, node):
        ventilation_widgets = {
            'Natural': self._build_window(node._states['Natural']),
            'Mechanical': self._build_mechanical(node._states['Mechanical']),
        }
        for name, widget in ventilation_widgets.items():
            widget.layout.visible = False

        ventilation_w = widgets.ToggleButtons(
            options=ventilation_widgets.keys(),
        )

        def toggle_ventilation(value):
            for name, widget in ventilation_widgets.items():
                widget.layout.display = 'none'

            node.dcs_select(value)

            widget = ventilation_widgets[value]
            widget.layout.visible = True
            widget.layout.display = 'block'

        ventilation_w.observe(lambda event: toggle_ventilation(event['new']), 'value')
        toggle_ventilation(ventilation_w.value)

        w = collapsible(
            [widget_group([[widgets.Label('Ventilation type'), ventilation_w]])]
            + list(ventilation_widgets.values()),
            title='Ventilation scheme'
        )
        return w

    def present(self):
        return self.widget


baseline_model = models.ExposureModel(
    concentration_model=models.ConcentrationModel(
        room=models.Room(volume=75),
        ventilation=models.WindowOpening(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0,24),(293.15,)),
            outside_temp=models.PiecewiseConstant((0,24),(283.15,)),
            cd_b=0.6, window_height=1.6, opening_length=0.6,
        ),
        infected=models.InfectedPopulation(
            number=1,
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(((8, 12), (13, 17))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            expiration=models.Expiration.types['Unmodulated Vocalization'],
        ),
    ),
    exposed=models.Population(
        number=10,
        presence=models.SpecificInterval(((8, 12), (13, 17))),
        activity=models.Activity.types['Light activity'],
        mask=models.Mask.types['No mask'],
    ),
)


class CARAStateBuilder(state.StateBuilder):
    def build_type_Mask(self, _: dataclasses.Field):
        return state.DataclassStatePredefined(
            models.Mask,
            choices=models.Mask.types,
        )

    def build_type_Ventilation(self, _: dataclasses.Field):
        s = state.DataclassStateNamed(
            states={
                'Natural': self.build_generic(models.WindowOpening),
                'Mechanical': self.build_generic(models.HVACMechanical),
            },
            state_builder=self,
        )
        # Initialise the HVAC state
        s._states['Mechanical'].dcs_update_from(
            models.HVACMechanical(models.PeriodicInterval(120, 120), 500.)
        )
        return s


class ExpertApplication:
    def __init__(self):
        default_scenario = state.DataclassInstanceState(
                models.ExposureModel,
                state_builder=CARAStateBuilder(),
            )
        default_scenario.dcs_update_from(baseline_model)
        # For the time-being, we have to initialise the select states. Careful
        # as values might not correspond to what the baseline model says.
        default_scenario.concentration_model.infected.mask.dcs_select('No mask')
        self.scenarios = (default_scenario,)
        self.scenario_names = ('Scenario 1',)
        self.tab_views = (WidgetView(default_scenario),)
        self.selected_tab = 0
        self.tabs = (widgets.VBox(children=(self.build_settings_menu(0), self.tab_views[0].present())),)
        self.tab_widget = widgets.Tab()
        self.update_tab_widget()
        self.comparison_view = ComparisonView()

    def display_titles(self):
        for i, name in enumerate(self.scenario_names):
            self.tab_widget.set_title(i, name)

    def update_tab_widget(self):
        self.tab_widget.children = self.tabs
        self.display_titles()

    def build_settings_menu(self, tab_index):
        delete_button = widgets.Button(description='Delete Scenario', button_style='danger')
        rename_text_field = widgets.Text(description='Rename Scenario:', value=self.scenario_names[tab_index],
                                         style={'description_width': 'auto'})
        duplicate_button = widgets.Button(description='Duplicate Scenario', button_style='success')

        def on_delete_click(b):
            self.scenario_names = tuple_without_index(self.scenario_names, tab_index)
            self.scenarios = tuple_without_index(self.scenarios, tab_index)
            self.tab_views = tuple_without_index(self.tab_views, tab_index)
            self.selected_tab = min(0, self.selected_tab - 1)
            self.tabs = tuple(widgets.VBox(children=(self.build_settings_menu(i), view.present()))
                              for i, view in enumerate(self.tab_views))
            self.update_tab_widget()

        def on_rename_text_field(change):
            self.scenario_names = tuple(change['new'] if i == tab_index else value
                                        for i, value in enumerate(self.scenario_names))
            self.update_tab_widget()

        def on_duplicate_click(b):
            self.scenario_names += (self.scenario_names[tab_index] + " (copy)",)
            new_scenario = state.DataclassInstanceState(
                models.ExposureModel,
                state_builder=CARAStateBuilder(),
            )
            new_scenario.dcs_update_from(self.scenarios[tab_index].dcs_instance())
            self.scenarios += (new_scenario,)

            self.tab_views += (WidgetView(new_scenario),)
            self.tabs += (widgets.VBox(children=(self.build_settings_menu(len(self.scenario_names) - 1),
                                                 self.tab_views[-1].present())),)
            self.update_tab_widget()

        delete_button.on_click(on_delete_click)
        duplicate_button.on_click(on_duplicate_click)
        rename_text_field.observe(on_rename_text_field, 'value')
        buttons = duplicate_button if tab_index == 0 else widgets.HBox(children=(duplicate_button, delete_button))
        return widgets.VBox(children=(buttons, rename_text_field))

    @property
    def widget(self):
        self.comparison_view.update_plot()
        return widgets.VBox(children=(self.tab_widget, self.comparison_view.figure.canvas))


class ComparisonView:
    def __init__(self):
        self.figure = self.initialize_figure()
        self.ax = self.initialize_axis()

    @staticmethod
    def initialize_figure() -> matplotlib.figure.Figure:
        figure = matplotlib.figure.Figure(figsize=(9, 6))
        matplotlib.interactive(False)
        ipympl.backend_nbagg.new_figure_manager_given_figure(uuid.uuid1(), figure)
        figure.canvas.toolbar_visible = True
        figure.canvas.toolbar.collapsed = True
        figure.canvas.footer_visible = False
        figure.canvas.header_visible = False
        return figure

    def initialize_axis(self) -> matplotlib.figure.Axes:
        ax = self.figure.add_subplot(1, 1, 1)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.set_xlabel('Time (hours)')
        ax.set_ylabel('Concentration ($q/m^3$)')
        ax.set_title('Concentration of infectious quanta aerosols')
        return ax

    def update_plot(self, conc_models: typing.Tuple[models.ConcentrationModel], labels: typing.Tuple[str]):
        self.figure.clf()
        # Hard-coded 8:00-17:00 interval
        ts = np.linspace(8, 17)
        concentrations = [[conc_model.concentration(t) for t in ts] for conc_model in conc_models]
        for concentration in concentrations:
            self.ax.plot(ts, concentration)

        top = max(3., max([max(conc) for conc in concentrations]))
        self.ax.set_ylim(bottom=0., top=top)

        self.figure.legend(labels)

        self.figure.canvas.draw()


def tuple_without_index(t: typing.Tuple, index: int) -> typing.Tuple:
    return t[:index] + t[index + 1:]
