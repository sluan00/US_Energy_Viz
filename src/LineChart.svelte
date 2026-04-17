<script>
    import * as d3 from 'd3';
    import { createEventDispatcher } from 'svelte';

    export let fuelPrices;    // [{year, fuel, price}]
    export let elecPrices;    // [{year, price}] national avg cents/kWh
    export let selectedYear;
    const dispatch = createEventDispatcher();

    let margin = { top: 20, right: 80, bottom: 30, left: 50 };
    let width = 900;
    let height = 200;
    let chartW = width - margin.left - margin.right;
    let chartH = height - margin.top - margin.bottom;

    let xAxisEl;
    let yAxisLeft;
    let yAxisRight;
    let dragging = false;
    let svgEl;

    const fuelColors = {
        'Coal': '#5c5c5c',
        'Natural Gas': '#e07b39',
        'Petroleum': '#a3483b'
    };

    $: years = [...new Set(fuelPrices.map(d => d.year))].sort();
    $: minYear = d3.min(years) || 1990;
    $: maxYear = d3.max(years) || 2024;

    $: xScale = d3.scaleLinear()
        .domain([minYear, maxYear])
        .range([0, chartW]);

    // Left axis: fuel price $/MMBtu
    $: yScaleLeft = d3.scaleLinear()
        .domain([0, d3.max(fuelPrices, d => d.price) * 1.1 || 15])
        .range([chartH, 0]);

    // Right axis: electricity price cents/kWh
    $: yScaleRight = d3.scaleLinear()
        .domain([0, d3.max(elecPrices, d => d.price) * 1.1 || 20])
        .range([chartH, 0]);

    // Line generators
    $: fuelLine = d3.line()
        .x(d => xScale(d.year))
        .y(d => yScaleLeft(d.price))
        .defined(d => d.price > 0);

    $: elecLine = d3.line()
        .x(d => xScale(d.year))
        .y(d => yScaleRight(d.price))
        .defined(d => d.price > 0);

    // Group fuel prices by fuel type
    $: fuelGroups = d3.groups(fuelPrices, d => d.fuel);

    $: {
        d3.select(xAxisEl).call(d3.axisBottom(xScale).tickFormat(d3.format('d')));
        d3.select(yAxisLeft).call(d3.axisLeft(yScaleLeft).ticks(5));
        d3.select(yAxisRight).call(d3.axisRight(yScaleRight).ticks(5));
    }

    function handleMouseDown(event) {
        dragging = true;
        updateYear(event);
    }

    function handleMouseMove(event) {
        if (dragging) updateYear(event);
    }

    function handleMouseUp() {
        dragging = false;
    }

    function updateYear(event) {
        if (!svgEl) return;
        const rect = svgEl.getBoundingClientRect();
        const x = event.clientX - rect.left - margin.left;
        const year = Math.round(xScale.invert(Math.max(0, Math.min(chartW, x))));
        const clamped = Math.max(minYear, Math.min(maxYear, year));
        dispatch('yearChange', clamped);
    }
</script>

<svelte:window on:mouseup={handleMouseUp} on:mousemove={handleMouseMove} />

<svg {width} {height} bind:this={svgEl}>
    <g transform="translate({margin.left}, {margin.top})">
        <!-- Fuel price lines -->
        {#each fuelGroups as [fuel, data]}
            <path
                class="line"
                d={fuelLine(data)}
                stroke={fuelColors[fuel] || '#999'}
                fill="none"
                stroke-width={2}
            />
            <!-- Label at end -->
            {@const last = data[data.length - 1]}
            {#if last}
                <text
                    x={xScale(last.year) + 4}
                    y={yScaleLeft(last.price)}
                    fill={fuelColors[fuel]}
                    font-size="10"
                    dominant-baseline="middle"
                >{fuel}</text>
            {/if}
        {/each}

        <!-- Electricity price line (right axis) -->
        {#if elecPrices.length > 0}
            <path
                class="line elec-line"
                d={elecLine(elecPrices)}
                stroke="#60a5fa"
                fill="none"
                stroke-width={2.5}
                stroke-dasharray="6,3"
            />
            {@const lastE = elecPrices[elecPrices.length - 1]}
            {#if lastE}
                <text
                    x={xScale(lastE.year) + 4}
                    y={yScaleRight(lastE.price)}
                    fill="#60a5fa"
                    font-size="10"
                    dominant-baseline="middle"
                >kWh</text>
            {/if}
        {/if}

        <!-- Year selector line -->
        <line
            x1={xScale(selectedYear)}
            x2={xScale(selectedYear)}
            y1={0}
            y2={chartH}
            stroke="#fff"
            stroke-width={2}
            stroke-dasharray="4,2"
        />
        <text
            x={xScale(selectedYear)}
            y={-6}
            fill="#fff"
            font-size="12"
            text-anchor="middle"
            font-weight="bold"
        >{selectedYear}</text>

        <!-- Invisible drag area -->
        <rect
            x={0} y={0}
            width={chartW} height={chartH}
            fill="transparent"
            style="cursor: ew-resize;"
            on:mousedown={handleMouseDown}
            role="slider"
            tabindex="0"
            aria-valuenow={selectedYear}
        />

        <!-- Axes -->
        <g bind:this={xAxisEl} transform="translate(0, {chartH})" />
        <g bind:this={yAxisLeft} />
        <g bind:this={yAxisRight} transform="translate({chartW}, 0)" />

        <!-- Axis labels -->
        <text x={-35} y={-8} fill="#aaa" font-size="10">$/MMBtu</text>
        <text x={chartW - 5} y={-8} fill="#60a5fa" font-size="10" text-anchor="end">cents/kWh</text>
    </g>
</svg>

<style>
    .line {
        pointer-events: none;
    }
</style>
