<script>
    import * as d3 from 'd3';
    import { createEventDispatcher } from 'svelte';

    export let data; // [{source, generation, percent}]
    export let sourceColors;
    export let selectedSource;

    const dispatch = createEventDispatcher();

    let margin = { top: 5, right: 60, bottom: 20, left: 5 };
    let width = 420;
    let height = 200;
    let chartW = width - margin.left - margin.right;
    let chartH = height - margin.top - margin.bottom;

    $: total = d3.sum(data, d => d.generation);

    // Build stacked segments (horizontal stacked bar)
    $: segments = (() => {
        let x = 0;
        return data.map(d => {
            const w = total > 0 ? (d.generation / total) * chartW : 0;
            const seg = { source: d.source, x, width: w, percent: d.percent, generation: d.generation };
            x += w;
            return seg;
        });
    })();

    function handleClick(source) {
        dispatch('selectSource', source);
    }

    function formatMWh(val) {
        if (val >= 1e9) return (val / 1e9).toFixed(1) + 'B';
        if (val >= 1e6) return (val / 1e6).toFixed(1) + 'M';
        if (val >= 1e3) return (val / 1e3).toFixed(0) + 'K';
        return val.toFixed(0);
    }
</script>

<svg {width} {height}>
    <g transform="translate({margin.left}, {margin.top})">
        <!-- Stacked horizontal bar -->
        {#each segments as seg}
            <rect
                class="segment"
                class:selected={selectedSource === seg.source}
                class:dimmed={selectedSource && selectedSource !== seg.source}
                x={seg.x}
                y={0}
                width={Math.max(0, seg.width - 1)}
                height={40}
                fill={sourceColors[seg.source] || '#666'}
                on:click={() => handleClick(seg.source)}
                on:keydown={(e) => { if (e.key === 'Enter') handleClick(seg.source); }}
                role="button"
                tabindex="0"
            />
        {/each}

        <!-- Legend below the bar -->
        {#each data as d, i}
            {@const col = Math.floor(i / 4)}
            {@const row = i % 4}
            <g transform="translate({col * 200}, {55 + row * 28})">
                <rect
                    x={0} y={0}
                    width={14} height={14}
                    fill={sourceColors[d.source] || '#666'}
                    rx={2}
                    class="legend-swatch"
                    class:selected={selectedSource === d.source}
                    class:dimmed={selectedSource && selectedSource !== d.source}
                    on:click={() => handleClick(d.source)}
                    on:keydown={(e) => { if (e.key === 'Enter') handleClick(d.source); }}
                    role="button"
                    tabindex="0"
                />
                <text x={20} y={12} class="legend-text"
                    class:dimmed={selectedSource && selectedSource !== d.source}
                    on:click={() => handleClick(d.source)}
                    on:keydown={(e) => { if (e.key === 'Enter') handleClick(d.source); }}
                    role="button"
                    tabindex="0">
                    {d.source} ({d.percent.toFixed(1)}%)
                </text>
            </g>
        {/each}
    </g>
</svg>

<style>
    .segment {
        cursor: pointer;
        stroke: #1a1a2e;
        stroke-width: 1px;
        transition: opacity 0.15s;
    }

    .segment:hover {
        stroke: #fff;
        stroke-width: 2px;
    }

    .segment.selected {
        stroke: #fff;
        stroke-width: 2px;
    }

    .segment.dimmed {
        opacity: 0.3;
    }

    .legend-swatch {
        cursor: pointer;
    }

    .legend-swatch.dimmed {
        opacity: 0.3;
    }

    .legend-text {
        fill: #ccc;
        font-size: 12px;
        cursor: pointer;
    }

    .legend-text.dimmed {
        opacity: 0.3;
    }
</style>
