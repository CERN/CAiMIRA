/* Generate the concentration plot using d3 library. */
function draw_plot(svg_id) {

    // Used for controlling the short-range interactions 
    let button_full_exposure = document.getElementById("button_full_exposure");
    let button_hide_high_concentration = document.getElementById("button_hide_high_concentration");
    let long_range_checkbox = document.getElementById('long_range_cumulative_checkbox')
    let show_sr_legend = short_range_expirations.length > 0;

    var data_for_graphs = {
        'concentrations': [],
        'cumulative_doses': [],
        'long_range_cumulative_doses': [],
    }
    times.map((time, index) => data_for_graphs.concentrations.push({ 'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': concentrations[index]}));
    times.map((time, index) => data_for_graphs.cumulative_doses.push({ 'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': cumulative_doses[index]}));
    times.map((time, index) => data_for_graphs.long_range_cumulative_doses.push({ 'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': long_range_cumulative_doses[index]}));

    const tooltip_data_for_graphs = Object.fromEntries(Object.entries(data_for_graphs).filter(([key]) => !key.includes('long_range_cumulative_doses')));

    // Add main SVG element
    var plot_div = document.getElementById(svg_id);
    var vis = d3.select(plot_div).append('svg');

    var time_format = d3.timeFormat('%H:%M');
    // H:M time format for x axis.
    xRange = d3.scaleTime().domain([data_for_graphs.concentrations[0].hour, data_for_graphs.concentrations[data_for_graphs.concentrations.length - 1].hour]),
    xTimeRange = d3.scaleLinear().domain([data_for_graphs.concentrations[0].time, data_for_graphs.concentrations[data_for_graphs.concentrations.length - 1].time]),
    bisecHour = d3.bisector((d) => { return d.hour; }).left,

    yRange = d3.scaleLinear(),
    yCumulativeRange = d3.scaleLinear(),
    
    yAxis = d3.axisLeft(),
    yCumulativeAxis = d3.axisRight();

    // X axis declaration.
    var xAxisEl = vis.append('svg:g')
        .attr('class', 'x axis');

    // X axis label.
    var xAxisLabelEl = vis.append('text')
        .attr('class', 'x label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Time of day')

    // Y axis declaration.
    var yAxisEl = vis.append('svg:g')
        .attr('class', 'y axis');

    // Y axis label.
    var yAxisLabelEl = vis.append('svg:text')
        .attr('class', 'y label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Mean concentration (virions/m³)');

    // Y cumulative concentration axis declaration.
    var yAxisCumEl = vis.append('svg:g')
        .attr('class', 'y axis')
        .style("stroke-dasharray", "5 5");

    // Y cumulated concentration axis label.
    var yAxisCumLabelEl = vis.append('svg:text')
        .attr('class', 'y label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Mean cumulative dose (infectious virus)');

    // Legend for the plot elements - line and area.
    
    // Concentration line icon
    var legendLineIcon = vis.append('rect')
        .attr('width', 20)
        .attr('height', 3)
        .style('fill', '#1f77b4');
    // Concentration line text
    var legendLineText = vis.append('text')
        .text('Mean concentration')
        .style('font-size', '15px');

    // Cumulative dose line icon
    var legendCumulativeIcon = vis.append('line')
        .style("stroke-dasharray", "5 5") //dashed array for line
        .attr('stroke-width', '2')
        .style("stroke", '#1f77b4');
    // Cumulative dose line text
    var legendCumutiveText = vis.append('text')
        .text('Cumulative dose')
        .style('font-size', '15px');

    //  Area line icon
    var legendAreaIcon = vis.append('rect')
        .attr('width', 20)
        .attr('height', 15)
        .attr('fill', '#1f77b4')
        .attr('fill-opacity', '0.1');
    //  Area line text
    var legendAreaText = vis.append('text')
        .text('Presence of exposed person(s)')
        .style('font-size', '15px');

    sr_unique_activities = [...new Set(short_range_expirations)]
    if (show_sr_legend) {
        // Long-range cumulative dose line legend - line and area
        var legendLongCumulativeIcon = vis.append('line')
            .style("stroke-dasharray", "5 5") //dashed array for line
            .attr('stroke-width', '2')
            .style("stroke", 'purple')
            .attr('opacity', 0);
        var legendLongCumutiveText = vis.append('text')
            .text('Long-range cumulative dose')
            .style('font-size', '15px')
            .attr('opacity', 0);
        // Short-range area icon
        var legendShortRangeAreaIcon = {};
        sr_unique_activities.forEach((b, index) => {
        legendShortRangeAreaIcon[index] = vis.append('rect')
            .attr('width', 20)
            .attr('height', 15);
        // Short-range area icon colors
        if (sr_unique_activities[index] == 'Breathing') legendShortRangeAreaIcon[index].attr('fill', 'red').attr('fill-opacity', '0.2');
        else if (sr_unique_activities[index] == 'Speaking') legendShortRangeAreaIcon[index].attr('fill', 'green').attr('fill-opacity', '0.1');
        else legendShortRangeAreaIcon[index].attr('fill', 'blue').attr('fill-opacity', '0.1');
        });
        // Short-range area text
        var legendShortRangeText = {};
        sr_unique_activities.forEach((b, index) => {
            legendShortRangeText[index] = vis.append('text')
            .text('Short-range - ' + sr_unique_activities[index])
            .style('font-size', '15px');
        });
    }

    // Legend bounding
    if (show_sr_legend) legendBBox_height = 68 + 20 * sr_unique_activities.length;
    else legendBBox_height = 68;
    var legendBBox = vis.append('rect')
        .attr('width', 255)
        .attr('height', legendBBox_height)
        .attr('stroke', 'lightgrey')
        .attr('stroke-width', '2')
        .attr('rx', '5px')
        .attr('ry', '5px')
        .attr('stroke-linejoin', 'round')
        .attr('fill', 'none');

    var clip = vis.append("defs").append("svg:clipPath")
        .attr("id", "clip")
        .append("svg:rect");

    var draw_area = vis.append('svg:g')
        .attr('clip-path', 'url(#clip)');
    // Line representing the mean concentration.
    var lineFunc = d3.line();
    draw_area.append('svg:path')
        .attr('class', 'line')
        .attr('stroke', '#1f77b4')
        .attr('stroke-width', 2)
        .attr('fill', 'none');
    
    // Line representing the cumulative concentration.
    var lineCumulative = d3.line();
    var draw_cumulative_line = draw_area.append('svg:path')
        .attr('stroke', '#1f77b4')
        .attr('stroke-width', 2)
        .style("stroke-dasharray", "5 5")
        .attr('fill', 'none');

    // Line representing the long-range cumulative concentration.
    if (show_sr_legend) {
        var longRangeCumulative = d3.line();
        var draw_long_range_cumulative_line = draw_area.append('svg:path')
            .attr('stroke', 'purple')
            .attr('stroke-width', 2)
            .style("stroke-dasharray", "5 5")
            .attr('fill', 'none')
            .attr('opacity', 0);      
    }

    // Area representing the presence of exposed person(s).
    var exposedArea = {};
    var drawArea = {};
    exposed_presence_intervals.forEach((b, index) => {
        exposedArea[index] = d3.area();
        drawArea[index] = draw_area.append('svg:path')
            .attr('fill', '#1f77b4')
            .attr('fill-opacity', '0.1');
    });

    // Area representing the short-range interaction(s).
    var shortRangeArea = {};
    var drawShortRangeArea = {};
    short_range_intervals.forEach((b, index) => {
        shortRangeArea[index] = d3.area();
        drawShortRangeArea[index] = draw_area.append('svg:path');

        if (short_range_expirations[index] == 'Breathing') drawShortRangeArea[index].attr('fill', 'red').attr('fill-opacity', '0.2');
        else if (short_range_expirations[index] == 'Speaking') drawShortRangeArea[index].attr('fill', 'green').attr('fill-opacity', '0.1');
        else drawShortRangeArea[index].attr('fill', 'blue').attr('fill-opacity', '0.1');
    });

    // Tooltip.
    var focus = {}, tooltip_rect = {}, tooltip_time = {}, tooltip_concentration = {}, toolBox = {};
    for (const [concentration, data] of Object.entries(tooltip_data_for_graphs)) {

        focus[concentration] = vis.append('svg:g')
            .style('display', 'none');

        focus[concentration].append('circle')
            .attr('r', 3);

        tooltip_rect[concentration] = focus[concentration].append('rect')
            .attr('fill', 'white')
            .attr('stroke', '#000')
            .attr('width', 85)
            .attr('height', 50)
            .attr('y', -22)
            .attr('rx', 4)
            .attr('ry', 4);

        tooltip_time[concentration] = focus[concentration].append('text')
            .attr('id', 'tooltip-time')
            .attr('x', 18)
            .attr('y', -2);

        tooltip_concentration[concentration] = focus[concentration].append('text')
            .attr('id', 'tooltip-concentration')
            .attr('x', 18)
            .attr('y', 18);

        toolBox[concentration] = vis.append('rect')
            .attr('fill', 'none')
            .attr('pointer-events', 'all')
            .on('mouseover', () => { for (const [concentration, data] of Object.entries(focus)) focus[concentration].style('display', null); })
            .on('mouseout', () => { for (const [concentration, data] of Object.entries(focus)) focus[concentration].style('display', 'none'); })
            .on('mousemove', mousemove);;
    }

    function update_concentration_plot(concentration_data, cumulative_data) {
        yRange.domain([0., Math.max(...concentration_data)*1.1]);
        yAxisEl.transition().duration(1000).call(yAxis);

        yCumulativeRange.domain([0., Math.max(...cumulative_data)*1.1]);
        yAxisCumEl.transition().duration(1000).call(yCumulativeAxis)
        
        // Concentration line
        lineFunc.defined(d => !isNaN(d.concentration))
            .x(d => xTimeRange(d.time))
            .y(d => yRange(d.concentration));
        draw_area.select('.line')
            .transition()
            .duration(1000)
            .attr("d", lineFunc(data_for_graphs.concentrations));

        // Cumulative line.
        lineCumulative.defined(d => !isNaN(d.concentration))
            .x(d => xTimeRange(d.time))
            .y(d => yCumulativeRange(d.concentration));
        draw_cumulative_line.transition()
            .duration(1000)
            .attr("d", lineCumulative(data_for_graphs.cumulative_doses));
    
        // Long-range cumulative line.
        if (show_sr_legend) {
            longRangeCumulative.defined(d => !isNaN(d.concentration))
                .x(d => xTimeRange(d.time))
                .y(d => yCumulativeRange(d.concentration));
            draw_long_range_cumulative_line.transition()
                .duration(1000)
                .attr("d", lineCumulative(data_for_graphs.long_range_cumulative_doses));
        }

        // Area.
        exposed_presence_intervals.forEach((b, index) => {
            exposedArea[index].x(d => xTimeRange(d.time))
                .y0(graph_height - 50)
                .y1(d => yRange(d.concentration)
            );
            drawArea[index].transition().duration(1000).attr('d', exposedArea[index](data_for_graphs.concentrations.filter(d => {
                    return d.time >= b[0] && d.time <= b[1]
            })));
        });

        // Short-Range Area.
        short_range_intervals.forEach((b, index) => {
            shortRangeArea[index].x(d => xTimeRange(d.time))
                .y0(graph_height - 50)
                .y1(d => yRange(d.concentration));

            drawShortRangeArea[index].transition().duration(1000).attr('d', shortRangeArea[index](data_for_graphs.concentrations.filter(d => {
                return d.time >= b[0] && d.time <= b[1]
            })));
        });

    }

    function redraw() {

        // Define width and height according to the screen size.
        var div_width = plot_div.clientWidth;
        var div_height = plot_div.clientHeight;
        graph_width = div_width;
        graph_height = div_height
        if (div_width >= 900) { // For screens with width > 900px legend can be on the graph's right side.
            var margins = { top: 30, right: 20, bottom: 50, left: 60 };
            div_width = 900;
            graph_width = div_width * (2/3);
            const svg_margins = {'margin-left': '0rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        }
        else {
            var margins = { top: 30, right: 20, bottom: 50, left: 40 };
            div_width = div_width * 1.1
            graph_width = div_width * .9;
            graph_height = div_height * 0.65; // On mobile screen sizes we want the legend to be on the bottom of the graph.
            const svg_margins = {'margin-left': '-1rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        };

        // Use the extracted size to set the size of the SVG element.
        vis.attr("width", div_width)
            .attr('height', div_height);

        // SVG components according to the width and height.

        // clipPath: everything out of this area won't be drawn.
        clip.attr("x", margins.left)
            .attr("y", margins.top)
            .attr("width", graph_width - margins.right - margins.left)
            .attr("height", graph_height - margins.top - margins.bottom);

        // Axis ranges.
        xRange.range([margins.left, graph_width - margins.right]);
        xTimeRange.range([margins.left, graph_width - margins.right]);
        yRange.range([graph_height - margins.bottom, margins.top]);
        yCumulativeRange.range([graph_height - margins.bottom, margins.top]);

        // Axis.
        var xAxis = d3.axisBottom(xRange).tickFormat(d => time_format(d));
        yAxis.scale(yRange);
        yCumulativeAxis.scale(yCumulativeRange);

        xAxisEl.attr('transform', 'translate(0,' + (graph_height - margins.bottom) + ')')
            .call(xAxis);
        xAxisLabelEl.attr('x', (graph_width + margins.right) / 2)
            .attr('y', graph_height * 0.97);
        
        yAxisEl.attr('transform', 'translate(' + margins.left + ',0)');
        yAxisLabelEl.attr('x', (graph_height * 0.9 + margins.bottom) / 2)
            .attr('y', (graph_height + margins.left) * 0.9)
            .attr('transform', 'rotate(-90, 0,' + graph_height + ')');

        yAxisCumEl.attr('transform', 'translate(' + (graph_width - margins.right) + ',0)').call(yCumulativeAxis);
        yAxisCumLabelEl.attr('transform', 'rotate(-90, 0,' + graph_height + ')')
            .attr('x', (graph_height + margins.bottom) / 2);

        if (plot_div.clientWidth >= 900) {
            yAxisCumLabelEl.attr('transform', 'rotate(-90, 0,' + graph_height + ')')
                .attr('x', (graph_height + margins.bottom) / 2)
                .attr('y', 1.71 * graph_width);
        }
        else {
            yAxisCumLabelEl.attr('transform', 'rotate(-90, 0,' + graph_height + ')')
                .attr('x', (graph_height + margins.bottom * 0.55) / 2)
                .attr('y', graph_width + 290);
        }

        const size = 20;
        var legend_x_start = 50;
        const space_between_text_icon = 30;
        const text_height = 6;
        // Legend on right side.
        if (plot_div.clientWidth >= 900) {
            legendLineIcon.attr('x', graph_width + legend_x_start)
                .attr('y', margins.top + size);
            legendLineText.attr('x', graph_width + legend_x_start + space_between_text_icon)
                .attr('y', margins.top + size + text_height);

            legendCumulativeIcon.attr("x1", graph_width + legend_x_start)
                .attr("x2", graph_width + legend_x_start + 20)
                .attr("y1", margins.top + 2 * size)
                .attr("y2", margins.top + 2 * size);
            legendCumutiveText.attr('x', graph_width + legend_x_start + space_between_text_icon)
                .attr('y', margins.top + 2 * size + text_height);
            
            legendAreaIcon.attr('x', graph_width + legend_x_start)
                .attr('y', margins.top + (3 * size) - 15/2);
            legendAreaText.attr('x', graph_width + legend_x_start + space_between_text_icon)
                .attr('y', margins.top + 3 * size + text_height);
            
            if (show_sr_legend) {
                sr_unique_activities.forEach((b, index) => {
                    legendShortRangeAreaIcon[index].attr('x', graph_width + legend_x_start)
                        .attr('y', margins.top + (4 + index) * size - 15/2);
                    legendShortRangeText[index].attr('x', graph_width + legend_x_start + space_between_text_icon)
                        .attr('y', margins.top + (4 + index) * size + text_height);
                });
                legendLongCumulativeIcon.attr("x1", graph_width + legend_x_start)
                    .attr("x2", graph_width + legend_x_start + 20)
                    .attr("y1", margins.top + (4 + sr_unique_activities.length) * size)
                    .attr("y2", margins.top + (4 + sr_unique_activities.length) * size);
                legendLongCumutiveText.attr('x', graph_width + legend_x_start + space_between_text_icon)
                    .attr('y', margins.top + (4 + sr_unique_activities.length) * size +  + text_height); 
            }
            
            legendBBox.attr('x', graph_width * 1.07)
                .attr('y', margins.top * 1.2);
        }
        // Legend on the bottom.
        else {
            legend_x_start = 10;

            legendLineIcon.attr('x', legend_x_start)
                .attr('y', graph_height + size);
            legendLineText.attr('x', legend_x_start + space_between_text_icon)
                .attr('y', graph_height + size + text_height);

            legendCumulativeIcon.attr("x1", legend_x_start)
                .attr("x2", legend_x_start + 20)
                .attr("y1", graph_height + 2 * size)
                .attr("y2", graph_height + 2 * size);
            legendCumutiveText.attr('x', legend_x_start + space_between_text_icon)
                .attr('y', graph_height + 2 * size + text_height);

            legendAreaIcon.attr('x', legend_x_start)
                .attr('y', graph_height + 3 * size - 15/2);
            legendAreaText.attr('x', legend_x_start + space_between_text_icon)
                .attr('y', graph_height + 3 * size + text_height);

            if (show_sr_legend) {
                sr_unique_activities.forEach((b, index) => {
                    legendShortRangeAreaIcon[index].attr('x', legend_x_start)
                        .attr('y', graph_height + (4 + index) * size - 15/2);
                    legendShortRangeText[index].attr('x', legend_x_start + space_between_text_icon)
                        .attr('y', graph_height + (4 + index) * size + text_height);
                });
                legendLongCumulativeIcon.attr("x1", legend_x_start)
                    .attr("x2", legend_x_start + 20)
                    .attr("y1", graph_height + (4 + sr_unique_activities.length) * size)
                    .attr("y2", graph_height + (4 + sr_unique_activities.length) * size)
                legendLongCumutiveText.attr('x', legend_x_start + space_between_text_icon)
                    .attr('y', graph_height + (4 + sr_unique_activities.length) * size + text_height);
            }

            legendBBox.attr('x', 1)
                .attr('y', graph_height + 6);
        }

        // ToolBox.
        for (const [concentration, data] of Object.entries(tooltip_data_for_graphs)) {
            toolBox[concentration].attr('width', graph_width - margins.right)
                .attr('height', graph_height);
        }

    }

    if (show_sr_legend) {
        long_range_checkbox.addEventListener("click", () => {
            if (long_range_checkbox.checked) {
                draw_long_range_cumulative_line.transition().duration(1000).attr("opacity", 1);
                legendBBox.transition().duration(1000).attr("height", legendBBox_height + 20);
                legendLongCumulativeIcon.transition().duration(1000).attr("opacity", 1);
                legendLongCumutiveText.transition().duration(1000).attr("opacity", 1);
            }
            else {
                draw_long_range_cumulative_line.transition().duration(1000).attr("opacity", 0);
                legendBBox.transition().duration(1000).attr("height", legendBBox_height);
                legendLongCumulativeIcon.transition().duration(1000).attr("opacity", 0);
                legendLongCumutiveText.transition().duration(1000).attr("opacity", 0);
            }
        });
    };

    if (button_full_exposure) {
        button_full_exposure.addEventListener("click", () => {
            update_concentration_plot(concentrations, cumulative_doses);
            button_full_exposure.disabled = true;
            button_hide_high_concentration.disabled = false;
        });
    }
    if (button_hide_high_concentration) {
        button_hide_high_concentration.addEventListener("click", () => {
            update_concentration_plot(concentrations_zoomed, long_range_cumulative_doses);
            button_full_exposure.disabled = false;
            button_hide_high_concentration.disabled = true;
        });
    }

    function mousemove() {
        for (const [scenario, data] of Object.entries(tooltip_data_for_graphs)) {
            if (d3.pointer(event)[0] < graph_width / 2) {
                tooltip_rect[scenario].attr('x', 10)
                tooltip_time[scenario].attr('x', 18)
                tooltip_concentration[scenario].attr('x', 18);
            }
            else {
                tooltip_rect[scenario].attr('x', -90)
                tooltip_time[scenario].attr('x', -82)
                tooltip_concentration[scenario].attr('x', -82)
            }
        }
        // Concentration line
        var x0 = xRange.invert(d3.pointer(event, this)[0]),
            i = bisecHour(data_for_graphs.concentrations, x0, 1),
            d0 = data_for_graphs.concentrations[i - 1],
            d1 = data_for_graphs.concentrations[i];
        if (d1) {
            var d = x0 - d0.hour > d1.hour - x0 ? d1 : d0;
            focus.concentrations.attr('transform', 'translate(' + xRange(d.hour) + ',' + yRange(d.concentration) + ')');
            focus.concentrations.select('#tooltip-time').text('x = ' + time_format(d.hour));
            focus.concentrations.select('#tooltip-concentration').text('y = ' + d.concentration.toFixed(2));
        }
        // Cumulative line
        var x0 = xRange.invert(d3.pointer(event, this)[0]),
            i = bisecHour(data_for_graphs.cumulative_doses, x0, 1),
            d0 = data_for_graphs.cumulative_doses[i - 1],
            d1 = data_for_graphs.cumulative_doses[i];
        if (d1 && d1.concentration) {
            var d = x0 - d0.hour > d1.hour - x0 ? d1 : d0;
            focus.cumulative_doses.attr('transform', 'translate(' + xRange(d.hour) + ',' + yCumulativeRange(d.concentration) + ')');
            focus.cumulative_doses.select('#tooltip-time').text('x = ' + time_format(d.hour));
            focus.cumulative_doses.select('#tooltip-concentration').text('y = ' + d.concentration.toFixed(2));
        }
    }

    // Draw for the first time to initialize.
    redraw();
    update_concentration_plot(concentrations, cumulative_doses);

    // Redraw based on the new size whenever the browser window is resized.
    window.addEventListener("resize", e => {
        redraw();
        if (button_full_exposure && button_full_exposure.disabled) update_concentration_plot(concentrations, cumulative_doses);
        else update_concentration_plot(concentrations_zoomed, long_range_cumulative_doses)
    });
}


// Generate the alternative scenarios plot using d3 library.
// 'alternative_scenarios' is a dictionary with all the alternative scenarios 
// 'times' is a list of times for all the scenarios
// The method is prepared to consider short-range interactions if needed.
function draw_alternative_scenarios_plot(concentration_plot_svg_id, alternative_plot_svg_id) {
    // H:M format
    var time_format = d3.timeFormat('%H:%M');
    // D3 array of ten categorical colors represented as RGB hexadecimal strings.
    var colors = d3.schemeAccent;

    // Used for controlling the short-range interactions 
    let button_full_exposure = document.getElementById("button_alternative_full_exposure");
    let button_hide_high_concentration = document.getElementById("button_alternative_hide_high_concentration");

    // Variable for the highest concentration for all the scenarios
    var highest_concentration = 0.

    var data_for_scenarios = {}
    for (scenario in alternative_scenarios) {
        scenario_concentrations = alternative_scenarios[scenario].concentrations;

        highest_concentration = Math.max(highest_concentration, Math.max(...scenario_concentrations))

        var data = []
        times.map((time, index) => data.push({ 'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': scenario_concentrations[index] }))

        // Add data into lines dictionary
        data_for_scenarios[scenario] = data
    }

    // We need one scenario to get the time range
    var first_scenario = Object.values(data_for_scenarios)[0]

    // Add main SVG element
    var alternative_plot_div = document.getElementById(alternative_plot_svg_id);
    var vis = d3.select(alternative_plot_div).append('svg');

    var xRange = d3.scaleTime().domain([first_scenario[0].hour, first_scenario[first_scenario.length - 1].hour]);
    var xTimeRange = d3.scaleLinear().domain([times[0], times[times.length - 1]]);
    var bisecHour = d3.bisector((d) => { return d.hour; }).left;

    var yRange = d3.scaleLinear();
    var yAxis = d3.axisLeft();

    // X axis.
    var xAxisEl = vis.append('svg:g')
        .attr('class', 'x axis');

    // X axis label.
    var xAxisLabelEl = vis.append('text')
        .attr('class', 'x label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Time of day');

    // Y axis declaration.
    var yAxisEl = vis.append('svg:g')
         .attr('class', 'y axis');

    // Y axis label.
    var yAxisLabelEl = vis.append('svg:text')
        .attr('class', 'y label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Mean concentration (virions/m³)');

    // Legend bounding box.
    max_key_length = Math.max(...(Object.keys(data_for_scenarios).map(el => el.length)));
    var legendBBox = vis.append('rect')
        .attr('width', 8.25 * max_key_length )
        .attr('height', 25 * (Object.keys(data_for_scenarios).length))
        .attr('stroke', 'lightgrey')
        .attr('stroke-width', '2')
        .attr('rx', '5px')
        .attr('ry', '5px')
        .attr('stroke-linejoin', 'round')
        .attr('fill', 'none');

    var clip = vis.append("defs").append("svg:clipPath")
        .attr("id", "clip")
        .append("svg:rect");

    var draw_area = vis.append('svg:g')
        .attr('clip-path', 'url(#clip)');

    // Line representing the mean concentration for each scenario.
    var lineFuncs = {}, draw_lines  = {}, label_icons = {}, label_text = {};
    for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {
        var scenario_index = Object.keys(data_for_scenarios).indexOf(scenario_name)

        // Line representing the mean concentration.
        lineFuncs[scenario_name] = d3.line();

        draw_lines[scenario_name] = draw_area.append('svg:path')
            .attr("stroke", colors[scenario_index])
            .attr('stroke-width', 2)
            .attr('fill', 'none');

        // Legend for the plot elements - lines.
        label_icons[scenario_name] = vis.append('rect')
            .attr('width', 20)
            .attr('height', 3)
            .style('fill', colors[scenario_index]);

        label_text[scenario_name] = vis.append('text')
            .text(scenario_name)
            .style('font-size', '15px');

    }

    // Tooltip.
    var focus = {}, tooltip_rect = {}, tooltip_time = {}, tooltip_concentration = {}, toolBox = {};
    for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {

        focus[scenario_name] = vis.append('svg:g')
            .style('display', 'none');

        focus[scenario_name].append('circle')
            .attr('r', 3);

        tooltip_rect[scenario_name] = focus[scenario_name].append('rect')
            .attr('fill', 'white')
            .attr('stroke', '#000')
            .attr('width', 80)
            .attr('height', 50)
            .attr('y', -22)
            .attr('rx', 4)
            .attr('ry', 4);

        tooltip_time[scenario_name] = focus[scenario_name].append('text')
            .attr('id', 'tooltip-time')
            .attr('y', -2);

        tooltip_concentration[scenario_name] = focus[scenario_name].append('text')
            .attr('id', 'tooltip-concentration')
            .attr('y', 18);

        toolBox[scenario_name] = vis.append('rect')
            .attr('fill', 'none')
            .attr('pointer-events', 'all')
            .on('mouseover', () => { for (const [scenario_name, data] of Object.entries(focus)) focus[scenario_name].style('display', null); })
            .on('mouseout', () => { for (const [scenario_name, data] of Object.entries(focus)) focus[scenario_name].style('display', 'none'); })
            .on('mousemove', mousemove);
    }

    function update_alternative_concentration_plot(concentration_data) {
        var highest_concentration = 0.

        for (scenario in alternative_scenarios) {
            scenario_concentrations = alternative_scenarios[scenario][concentration_data];
            highest_concentration = Math.max(highest_concentration, Math.max(...scenario_concentrations));
        }

        yRange.domain([0., highest_concentration*1.1]);
        yAxisEl.transition().duration(1000).call(yAxis);

        for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {
            // Lines.
            lineFuncs[scenario_name].defined(d => !isNaN(d.concentration))
                .x(d => xTimeRange(d.time))
                .y(d => yRange(d.concentration));
            draw_lines[scenario_name].transition().duration(1000).attr("d", lineFuncs[scenario_name](data));
        }
    }

    var graph_width;
    var graph_height;

    function redraw() {
        // Define width and height according to the screen size.
        var div_width = document.getElementById(concentration_plot_svg_id).clientWidth;
        var div_height = document.getElementById(concentration_plot_svg_id).clientHeight;
        graph_width = div_width;
        graph_height = div_height
        if (div_width >= 1200) { // For screens with width > 900px legend can be on the graph's right side.
            var margins = { top: 30, right: 20, bottom: 50, left: 60 };
            div_width = 1200;
            graph_width = 600;
            const svg_margins = {'margin-left': '0rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        }
        else {
            var margins = { top: 30, right: 20, bottom: 50, left: 40 };
            div_width = div_width * 1.1
            graph_width = div_width * .95;
            graph_height = div_height * 0.65; // On mobile screen sizes we want the legend to be on the bottom of the graph.
            const svg_margins = {'margin-left': '-1rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        };

        // Use the extracted size to set the size of the SVG element.
        vis.attr("width", div_width)
            .attr('height', div_height);

        // SVG components according to the width and height.
        // clipPath: everything out of this area won't be drawn.
        clip.attr("x", margins.left)
            .attr("y", margins.top)
            .attr("width", graph_width - margins.right - margins.left)
            .attr("height", graph_height - margins.top - margins.bottom);

        // Axis ranges.
        xRange.range([margins.left, graph_width - margins.right]);
        xTimeRange.range([margins.left, graph_width - margins.right]);
        yRange.range([graph_height - margins.bottom, margins.top]);

        var legend_x_start = 25;
        const space_between_text_icon = 30;
        const text_height = 6;
        for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {
            var scenario_index = Object.keys(data_for_scenarios).indexOf(scenario_name)
            // Legend on right side.
            var size = 20 * (scenario_index + 1);
            if (document.getElementById(concentration_plot_svg_id).clientWidth >= 900) {
                label_icons[scenario_name].attr('x', graph_width + legend_x_start)
                    .attr('y', margins.top + size);
                label_text[scenario_name].attr('x', graph_width + legend_x_start + space_between_text_icon)
                    .attr('y', margins.top + size  + text_height);
            }
            // Legend on the bottom.
            else {
                legend_x_start = 10;

                label_icons[scenario_name].attr('x', legend_x_start)
                    .attr('y', graph_height + size);
                label_text[scenario_name].attr('x', legend_x_start + space_between_text_icon)
                    .attr('y', graph_height + size  + text_height);
            }

        }

        // Axis.
        var xAxis = d3.axisBottom(xRange).tickFormat(d => time_format(d));
        yAxis.scale(yRange);

        xAxisEl.attr('transform', 'translate(0,' + (graph_height - margins.bottom) + ')')
            .call(xAxis);
        xAxisLabelEl.attr('x', (graph_width + margins.right) / 2)
            .attr('y', graph_height * 0.97)

        yAxisEl.attr('transform', 'translate(' + margins.left + ',0)')
            .call(yAxis);
        yAxisLabelEl.attr('transform', 'rotate(-90, 0,' + graph_height + ')')
            .attr('x', (graph_height * 0.9 + margins.bottom) / 2)
            .attr('y', (graph_height + margins.left) * 0.90);

        // Legend on right side.
        if (document.getElementById(concentration_plot_svg_id).clientWidth >= 900) {
            legendBBox.attr('x', graph_width * 1.02)
                .attr('y', margins.top * 1.15);
            
        }
        // Legend on the bottom.
        else {
            legendBBox.attr('x', 1)
                .attr('y', graph_height * 1.02)
        }

        // ToolBox.
        for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {
            toolBox[scenario_name].attr('width', graph_width - margins.right)
                .attr('height', graph_height);
        }
    }

    if (button_full_exposure) {
        button_full_exposure.addEventListener("click", () => {
            update_alternative_concentration_plot('concentrations');
            button_full_exposure.disabled = true;
            button_hide_high_concentration.disabled = false;
        });
    }
    if (button_hide_high_concentration) {
            button_hide_high_concentration.addEventListener("click", () => {
            update_alternative_concentration_plot('concentrations_zoomed');
            button_full_exposure.disabled = false;
            button_hide_high_concentration.disabled = true;
        });
    }

    function mousemove() {
        for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {
            if (d3.pointer(event)[0] < graph_width / 2) {
                tooltip_rect[scenario_name].attr('x', 10)
                tooltip_time[scenario_name].attr('x', 18)
                tooltip_concentration[scenario_name].attr('x', 18);
            }
            else {
                tooltip_rect[scenario_name].attr('x', -90)
                tooltip_time[scenario_name].attr('x', -82)
                tooltip_concentration[scenario_name].attr('x', -82)
            }
            var x0 = xRange.invert(d3.pointer(event, this)[0]),
                i = bisecHour(data, x0, 1),
                d0 = data[i - 1],
                d1 = data[i],
                d = x0 - d0.hour > d1.hour - x0 ? d1 : d0;
            focus[scenario_name].attr('transform', 'translate(' + xRange(d.hour) + ',' + yRange(d.concentration) + ')');
            focus[scenario_name].select('#tooltip-time').text('x = ' + time_format(d.hour));
            focus[scenario_name].select('#tooltip-concentration').text('y = ' + d.concentration.toFixed(2));
        }
    }

    // Draw for the first time to initialize.
    redraw();
    update_alternative_concentration_plot('concentrations');

    // Redraw based on the new size whenever the browser window is resized.
    window.addEventListener("resize", e => {
        redraw();
        if (button_full_exposure && button_full_exposure.disabled) update_alternative_concentration_plot('concentrations');
        else update_alternative_concentration_plot('concentrations')
    });
}

function copy_clipboard(shareable_link) {

    $("#mobile_link").attr('title', 'Copied!')
          .tooltip('_fixTitle')
          .tooltip('show');
          
    navigator.clipboard.writeText(shareable_link);
}