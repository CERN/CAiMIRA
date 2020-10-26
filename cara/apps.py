import typing
import uuid

import ipympl.backend_nbagg
import ipywidgets as widgets
import numpy as np
import matplotlib
import matplotlib.figure

from cara import models
from cara import state


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

    def update(self, model: models.Model):
        resolution = 600
        ts = np.linspace(0, 10, resolution)
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
            ax.set_ymargin(0.2)
            # ax.set_ylim(bottom=0)
        else:
            self.ax.ignore_existing_data_limits = True
            self.line.set_data(ts, concentration)
            self.ax.relim()
            self.ax.autoscale_view()
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
        self.widget.children += (self.out, )
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
            ])
        ], 'Results', start_collapsed=False)

        # Join inputs and outputs together in a single widget for convenience.
        self.widget.children += (self.widgets['results'], )

    def prepare_output(self):
        pass

    def update(self):
        model = self.model_state.dcs_instance()
        for plot in self.plots:
            plot.update(model)

    def _build_widget(self, node):
        self.widget.children += (self._build_room(node.room),)
        self.widget.children += (self._build_ventilation(node.ventilation),)
        self.widget.children += (self._build_infected(node.infected),)
        self.widget.children += (self._build_exposed(node),)

    def _build_exposed(self, node):
        return collapsible(
            [self._build_activity(node.exposed_activity)],
            title="Exposed"
        )

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

    def _build_window(self, node):
        period = widgets.IntSlider(value=node.period, min=0, max=240)
        interval = widgets.IntSlider(value=node.duration, min=0, max=240)

        def on_period_change(change):
            node.period = change['new']

        def on_interval_change(change):
            node.duration = change['new']

        # TODO: Link the state back to the widget, not just the other way around.
        period.observe(on_period_change, names=['value'])
        interval.observe(on_interval_change, names=['value'])

        return widget_group(
                [
                    [widgets.Label('Open every n minutes'), period],
                    [widgets.Label('For how long'), interval],
                 ]
            )

    def _build_hepa(self, node):
        period = widgets.IntSlider(value=node.period, min=0, max=240)
        interval = widgets.IntSlider(value=node.duration, min=0, max=240)

        def on_period_change(change):
            node.period = change['new']

        def on_interval_change(change):
            node.duration = change['new']

        # TODO: Link the state back to the widget, not just the other way around.
        period.observe(on_period_change, names=['value'])
        interval.observe(on_interval_change, names=['value'])

        return widget_group(
                [
                    [widgets.Label('On every n minutes'), period],
                    [widgets.Label('For how long'), interval],
                 ]
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
            mask = models.Mask.types[change['new']]
            node.dcs_update_from(mask)
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
            'Natural': self._build_window(node),
            # 'HEPA': self._build_hepa(node)
        }
        for name, widget in ventilation_widgets.items():
            widget.layout.visible = False

        ventilation_w = widgets.ToggleButtons(
            options=ventilation_widgets.keys(),
        )

        def toggle_ventilation(value):
            for name, widget in ventilation_widgets.items():
                widget.layout.display = 'none'
            # if value == 'Natural':
            #     node.dcs_update_from(models.PeriodicWindow())
            # elif value == 'HEPA':
            #     node.dcs_update_from(models.PeriodicHEPA())
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


baseline_model = models.Model(
    room=models.Room(volume=75),
    ventilation=models.PeriodicWindow(
        period=120, duration=120, inside_temp=293, outside_temp=283, cd_b=0.6,
        window_height=1.6, opening_length=0.6,
    ),
    infected=models.InfectedPerson(
        virus=models.Virus.types['SARS_CoV_2'],
        present_times=((0, 4), (5, 8)),
        mask=models.Mask.types['No mask'],
        activity=models.Activity.types['Light exercise'],
        expiration=models.Expiration.types['Unmodulated Vocalization'],
    ),
    infected_occupants=1,
    exposed_occupants=10,
    exposed_activity=models.Activity.types['Light exercise'],
)


class ExpertApplication:
    def __init__(self):
        self.model_state = state.DataclassState(models.Model)
        self.model_state.dcs_update_from(baseline_model)
        self.view = WidgetView(self.model_state)

    @property
    def widget(self):
        return self.view.present()
