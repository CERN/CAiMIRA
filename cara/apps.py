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

            ax.text(0.5, 0.9, 'Without masks & window open', transform=ax.transAxes, ha='center')

            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)

            ax.set_xlabel('Time (hours)')
            ax.set_ylabel('Concentration ($q/m^3$)')
            ax.set_title('Concentration of infectious quanta aerosols')
            ax.set_ymargin(0.2)
            ax.set_ylim(bottom=0)
        else:
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
        if isinstance(node, state.DataclassState):
            if node._base == models.Ventilation:
                self.widget.children += (self._build_ventilation(node), )
            elif node._base == models.Room:
                self.widget.children += (self._build_room(node), )
            else:
                # Don't do anything with this state, but recurse down in case
                # its children want widgets.
                for name, child in node._data.items():
                    self._build_widget(child)

    def _build_room(self, node):
        room_volume = widgets.IntSlider(value=node.volume, min=10, max=150)
        mask_used = widgets.Checkbox(value=True, description='Mask worn')

        def on_value_change(change):
            node.volume = change['new']

        # TODO: Link the state back to the widget, not just the other way around.
        room_volume.observe(on_value_change, names=['value'])

        widget = collapsible(
            [widget_group(
                [[widgets.Label('Room volume'), room_volume]]
            )],
            title='Specification of workplace', start_collapsed=False,
        )
        return widget

    def _build_ventilation(self, node):
        ventilation_widgets = {
            'Natural': widgets.Label('Currently hard-coded to window-example from mathematica notebook'),
            'other': widgets.Label('Not yet implemented.')
        }
        for name, widget in ventilation_widgets.items():
            widget.layout.visible = False

        ventilation_w = widgets.ToggleButtons(
            options=ventilation_widgets.keys(),
        )

        def toggle_ventilation(value):
            for name, widget in ventilation_widgets.items():
                widget.layout.display = 'none'
            other = ventilation_widgets['other']
            widget = ventilation_widgets.get(value, other)
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
        self.model_state.dcs_update_from(
            baseline_model
        )
        self.view = WidgetView(self.model_state)
        # self._widget = widgets.Text("WIP")

    @property
    def widget(self):
        return self.view.present()
