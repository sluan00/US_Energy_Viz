<script>
    import * as d3 from 'd3';
    import { createEventDispatcher } from 'svelte';

    export let data; // [{state, generation}]
    export let selectedState;
    export let sourceColors;
    export let selectedSource;
    const dispatch = createEventDispatcher();

    let margin = { top: 5, right: 50, bottom: 20, left: 35 };
    let width = 420;
    let height = 250;
    let chartW = width - margin.left - margin.right;
    let chartH = height - margin.top - margin.bottom;

    let xAxisEl;
    let yAxisEl;

    $: states = data.map(d => d.state);

    $: yScale = d3.scaleBand()
        .domain(states)
        .range([0, chartH])
        .padding(0.12);

    $: xScale = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.generation) || 1])
        .range([0, chartW]);

    $: {
        d3.select(xAxisEl).call(d3.axisBottom(xScale).ticks(4).tickFormat(d => {
            if (d >= 1e9) return (d / 1e9).toFixed(0) + 'B';
            if (d >= 1e6) return (d / 1e6).toFixed(0) + 'M';
            return d;
        }));
        d3.select(yAxisEl).call(d3.axisLeft(yScale));
    }

    $: barColor = selectedSource ? (sourceColors[selectedSource] || '#10b981') : '#10b981';

    function handleClick(state) {
        dispatch('selectState', state);
    }
</script>

<svg {width} {height}>
    <g transform="translate({margin.left}, {margin.top})">
        {#each data as d}
            <rect
                class="bar"
                class:selected={selectedState === d.state}
                class:dimmed={selectedState && selectedState !== d.state}
                x={0}
                y={yScale(d.state)}
                width={xScale(d.generation)}
                height={yScale.bandwidth()}
                fill={barColor}
                on:click={() => handleClick(d.state)}
                on:keydown={(e) => { if (e.key === 'Enter') handleClick(d.state); }}
                role="button"
                tabindex="0"
            />
        {/each}

        <g bind:this={xAxisEl} transform="translate(0, {chartH})" />
        <g bind:this={yAxisEl} />
    </g>
</svg>

<style>
    .bar {
        cursor: pointer;
        transition: opacity 0.15s;
    }

    .bar:hover {
        stroke: #fff;
        stroke-width: 1.5px;
    }

    .bar.selected {
        stroke: #fff;
        stroke-width: 2px;
    }

    .bar.dimmed {
        opacity: 0.35;
    }
</style>
