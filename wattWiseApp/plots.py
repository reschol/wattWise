#TODO

def plot_layperson_friendly_profile(df, column_name, start_date):
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import matplotlib.patches as patches
    
    # Data preparation
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    start = pd.to_datetime(start_date).date()
    end = start + pd.Timedelta(days=14)
    df = df[(df.index.date >= start) & (df.index.date <= end)]
    df['Stunde'] = df.index.hour
    df['Wochentag'] = df.index.weekday
    df['Typ'] = df['Wochentag'].apply(lambda x: 'Wochenende' if x >= 5 else 'Werktag')
    
    # Set a clean, readable style
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Create a figure with a single plot and simpler design
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Define better colors - blue for weekday, orange for weekend
    colors = {'Werktag': '#1f77b4', 'Wochenende': '#ff7f0e'}
    
    # Calculate statistics for visualization
    hourly_stats = {}
    
    for typ in ['Werktag', 'Wochenende']:
        typ_data = df[df['Typ'] == typ]
        hourly_stats[typ] = []
        
        for hour in range(24):
            hour_data = typ_data[typ_data['Stunde'] == hour]
            if len(hour_data) > 0:
                median = hour_data[column_name].median()
                # Calculate range statistics
                q25 = hour_data[column_name].quantile(0.25)
                q75 = hour_data[column_name].quantile(0.75)
                min_val = hour_data[column_name].min()
                max_val = hour_data[column_name].max()
                
                hourly_stats[typ].append({
                    'Stunde': hour,
                    'Median': median,
                    'Q25': q25,
                    'Q75': q75,
                    'Min': min_val,
                    'Max': max_val
                })
    
    # Define time periods for context
    time_periods = [
        {'name': 'Nacht', 'start': 0, 'end': 6, 'color': '#f8f8f8'},
        {'name': 'Morgen', 'start': 6, 'end': 12, 'color': '#fffde7'},
        {'name': 'Nachmittag', 'start': 12, 'end': 18, 'color': '#fff8e1'},
        {'name': 'Abend', 'start': 18, 'end': 24, 'color': '#f5f5f5'}
    ]
    
    # Add shaded background for time periods
    for period in time_periods:
        ax.axvspan(period['start'], period['end'], alpha=0.3, color=period['color'])
        # Add period label at top center of each zone
        mid_point = (period['start'] + period['end']) / 2
        ax.text(mid_point, 1.02, period['name'], ha='center', 
              transform=ax.get_xaxis_transform(), fontsize=12)
    
    # Plot both median lines and range indicators
    for typ in ['Werktag', 'Wochenende']:
        if hourly_stats[typ]:
            data = pd.DataFrame(hourly_stats[typ]).sort_values('Stunde')
            
            # Add min-max range with very light opacity
            ax.fill_between(
                data['Stunde'], 
                data['Min'], 
                data['Max'],
                color=colors[typ], 
                alpha=0.1, 
                label=f'Gesamter Bereich ({typ})'
            )
            
            # Add interquartile range (25%-75%) with medium opacity
            ax.fill_between(
                data['Stunde'], 
                data['Q25'], 
                data['Q75'],
                color=colors[typ], 
                alpha=0.3, 
                label=f'Üblicher Bereich ({typ})'
            )
            
            # Plot median line on top
            ax.plot(data['Stunde'], data['Median'], 
                   label=f'Typischer Verbrauch ({typ})',
                   color=colors[typ], linewidth=3)
    
    # Add title with proper spacing
    fig.suptitle("Ihr Stromverbrauch im Tagesverlauf", fontsize=16, fontweight='bold', y=0.98)
    
    # Add a clear subtitle with date range
    plt.figtext(0.5, 0.93, 
              f"{start.strftime('%d.%m.%Y')} bis {end.strftime('%d.%m.%Y')}", 
              ha="center", fontsize=12)
    
    ax.set_xlabel("Uhrzeit", fontsize=12)
    ax.set_ylabel("Stromverbrauch (kWh)", fontsize=12)
    
    # Set x-axis ticks to show all hours
    ax.set_xticks(range(0, 24, 2))
    ax.set_xticklabels([f"{h}:00" for h in range(0, 24, 2)])
    
    # Ensure y-axis starts at 0
    ax.set_ylim(bottom=0)
    
    # Add legend with better organization
    handles, labels = ax.get_legend_handles_labels()
    
    # Reorder legend items to group by type (Weekday/Weekend)
    by_label = dict(zip(labels, handles))
    
    # Create ordered lists based on the desired legend layout
    ordered_labels = []
    ordered_handles = []
    
    # First add Werktag items
    for prefix in ['Typischer Verbrauch', 'Üblicher Bereich', 'Gesamter Bereich']:
        key = f'{prefix} (Werktag)'
        if key in by_label:
            ordered_labels.append(key)
            ordered_handles.append(by_label[key])
    
    # Then add Wochenende items
    for prefix in ['Typischer Verbrauch', 'Üblicher Bereich', 'Gesamter Bereich']:
        key = f'{prefix} (Wochenende)'
        if key in by_label:
            ordered_labels.append(key)
            ordered_handles.append(by_label[key])
    
    # Create the legend with the ordered items
    ax.legend(ordered_handles, ordered_labels, loc='upper center', 
            bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=10)
    
    # Add explanatory text focusing on understanding patterns and ranges
    explanation = (
        "Die farbigen Linien zeigen Ihren typischen Stromverbrauch. "
        "Die dunkleren Bereiche zeigen, wie Ihr Verbrauch an den meisten Tagen schwankt. "
        "Die helleren Bereiche zeigen die maximale Spannweite Ihres Verbrauchs."
    )
    
    plt.figtext(0.5, -0.05, explanation, ha="center", fontsize=11, 
              wrap=True, bbox=dict(boxstyle="round,pad=0.5", fc="#f5f5f5", ec="#cccccc", alpha=0.7))
    
    # Apply tight layout but leave room for titles
    plt.tight_layout(rect=[0, 0, 1, 0.9])  # Reserve top 10% for titles
    plt.subplots_adjust(bottom=0.18)  # Increased bottom space for legend
    plt.savefig(column_name+"linechart_intervals.svg")

    # Save the plot as PNG for better compatibility
    png_path = f"/tmp/{column_name}_linechart_intervals.png"
    plt.savefig(png_path, dpi=150, bbox_inches='tight')
    #plt.show()


def plot_daily_patterns_comparison(df, column_name, start_date):
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import datetime
    
    # Set a clean style
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Data preparation
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    start = pd.to_datetime(start_date).date()
    end = start + pd.Timedelta(days=14)
    df = df[(df.index.date >= start) & (df.index.date <= end)]
    
    # Add helper columns
    df['Datum'] = df.index.date
    df['Stunde'] = df.index.hour
    df['Wochentag'] = df.index.weekday
    df['Wochenende'] = df['Wochentag'] >= 5
    
    # Create a larger figure
    fig, ax = plt.subplots(figsize=(14, 9))
    
    # Define colormap - use a subtle gradient
    # Weekday: Blues, Weekend: Oranges
    weekday_cmap = plt.cm.Blues
    weekend_cmap = plt.cm.Oranges
    
    # Get unique dates in the dataset
    unique_dates = sorted(df['Datum'].unique())
    
    # Calculate number of weekdays and weekends
    weekday_dates = [date for date in unique_dates if 
                    datetime.datetime.combine(date, datetime.time()).weekday() < 5]
    weekend_dates = [date for date in unique_dates if 
                    datetime.datetime.combine(date, datetime.time()).weekday() >= 5]
    
    # Create normalized color maps
    weekday_norm = plt.Normalize(0, max(len(weekday_dates)-1, 1))
    weekend_norm = plt.Normalize(0, max(len(weekend_dates)-1, 1))
    
    # Plot each day as a separate line
    for date in unique_dates:
        day_data = df[df['Datum'] == date]
        if len(day_data) > 0:
            # Sort by hour to ensure proper line
            day_data = day_data.sort_values('Stunde')
            
            # Check if weekend or weekday
            is_weekend = datetime.datetime.combine(date, datetime.time()).weekday() >= 5
            
            if is_weekend:
                # Get index in weekend list for color mapping
                weekend_idx = weekend_dates.index(date)
                color = weekend_cmap(weekend_norm(weekend_idx))
                zorder = 5  # Weekend days on top
            else:
                # Get index in weekday list for color mapping
                weekday_idx = weekday_dates.index(date)
                color = weekday_cmap(weekday_norm(weekday_idx))
                zorder = 2  # Weekday days below
            
            # Plot with thin line and some transparency
            ax.plot(day_data['Stunde'], day_data[column_name], 
                   color=color, alpha=0.5, linewidth=1, 
                   zorder=zorder)
    
    # Add median lines for weekdays and weekends for reference
    weekday_mean = df[~df['Wochenende']].groupby('Stunde')[column_name].mean()
    weekend_mean = df[df['Wochenende']].groupby('Stunde')[column_name].mean()
    
    # Plot mean lines with thicker lines
    if not weekday_mean.empty:
        ax.plot(weekday_mean.index, weekday_mean.values, 
               color='navy', linewidth=4, label='Durchschnitt Werktage', 
               zorder=10)
    
    if not weekend_mean.empty:
        ax.plot(weekend_mean.index, weekend_mean.values, 
               color='darkorange', linewidth=4, label='Durchschnitt Wochenende', 
               zorder=10)
    
    # Simple time markers at the top
    for hour in [0, 6, 12, 18, 24]:
        if hour < 24:
            ax.axvline(hour, color='gray', linestyle=':', alpha=0.5)
    
    # Simple time labels
    time_labels = ["Mitternacht", "6:00", "Mittag", "18:00", "Mitternacht"]
    for i, hour in enumerate([0, 6, 12, 18, 24]):
        if hour < 24:  # Don't add label for hour 24
            ax.text(hour, ax.get_ylim()[1]*1.02, time_labels[i], 
                  ha='center', va='bottom', fontsize=11, color='gray')
    
    # Add title with proper spacing - outside tight_layout control
    fig.suptitle("Tägliche Verbrauchsmuster", fontsize=18, fontweight='bold', y=0.98)
    
    # Add subtitle with date range - outside tight_layout control
    plt.figtext(0.5, 0.94, 
              f"{start.strftime('%d.%m.%Y')} bis {end.strftime('%d.%m.%Y')}", 
              ha="center", fontsize=14)
    
    # Set axis labels with larger font sizes
    ax.set_xlabel("Uhrzeit", fontsize=14, labelpad=10)
    ax.set_ylabel("Stromverbrauch (kWh)", fontsize=14, labelpad=10)
    
    # Set x-axis ticks to show hours clearly
    ax.set_xticks(range(0, 24, 2))
    ax.set_xticklabels([f"{h}" for h in range(0, 24, 2)], fontsize=11)
    ax.set_xlim(0, 23.5)
    
    # Ensure y-axis starts at 0 with larger tick labels
    ax.set_ylim(bottom=0)
    plt.yticks(fontsize=11)
    
    # Add a better positioned legend
    legend = ax.legend(loc='upper right', framealpha=0.9, fontsize=12)
    
    # Add simplified date-range text in the plot
    plt.figtext(0.15, 0.02, f"Werktage: {weekday_dates[0].strftime('%d.%m')} - {weekday_dates[-1].strftime('%d.%m')}", 
               color='navy', fontsize=12, fontweight='bold')
    
    plt.figtext(0.55, 0.02, f"Wochenenden: {weekend_dates[0].strftime('%d.%m')} - {weekend_dates[-1].strftime('%d.%m')}", 
               color='darkorange', fontsize=12, fontweight='bold')
    
    # Apply tight layout but leave room for titles
    plt.tight_layout(rect=[0, 0.05, 1, 0.9])
    plt.savefig(column_name+"linechart_raw_patterns.svg")
    #plt.show()


def plot_user_friendly_consumption_profile(df, column_name, start_date):
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import matplotlib.patches as patches
    from matplotlib.colors import LinearSegmentedColormap
    import matplotlib.gridspec as gridspec
    
    # Data preparation
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    start = pd.to_datetime(start_date).date()
    end = start + pd.Timedelta(days=14)
    df = df[(df.index.date >= start) & (df.index.date <= end)]
    df['Stunde'] = df.index.hour
    df['Wochentag'] = df.index.weekday
    df['Typ'] = df['Wochentag'].apply(lambda x: 'Wochenende' if x >= 5 else 'Werktag')
    
    # Set clean style
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Create figure with custom layout - main visualization plus side panel
    fig = plt.figure(figsize=(14, 8))
    
    # Create custom grid for layout
    gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1], figure=fig)
    
    # Main plot area (left)
    ax_main = fig.add_subplot(gs[0])
    
    # Side panel for context (right)
    ax_side = fig.add_subplot(gs[1])
    ax_side.axis('off')  # Hide axis for the side panel
    
    # Define distinct color schemes for weekday and weekend
    # Use blue shades for weekday
    weekday_colors = ["#deebf7", "#9ecae1", "#4292c6", "#08519c"]
    weekday_cmap = LinearSegmentedColormap.from_list("weekday", weekday_colors, N=100)
    
    # Use orange/red shades for weekend
    weekend_colors = ["#fee6ce", "#fdae6b", "#f16913", "#d94801"]
    weekend_cmap = LinearSegmentedColormap.from_list("weekend", weekend_colors, N=100)
    
    # Create heatmap data structure
    heatmap_data = {}
    hour_labels = []
    
    for typ in ['Werktag', 'Wochenende']:
        heatmap_data[typ] = np.zeros(24)
        
        for hour in range(24):
            hour_data = df[(df['Typ'] == typ) & (df['Stunde'] == hour)]
            if len(hour_data) > 0:
                heatmap_data[typ][hour] = hour_data[column_name].median()
    
    # Normalize separately for each type to ensure good color distribution
    for typ in ['Werktag', 'Wochenende']:
        typ_max = np.max(heatmap_data[typ])
        if typ_max > 0:
            heatmap_data[typ] = heatmap_data[typ] / typ_max
    
    # Create hour labels with simplified time format
    hour_labels = []
    for h in range(24):
        if h == 0:
            hour_labels.append("Mitternacht")
        elif h == 12:
            hour_labels.append("Mittag")
        elif h % 3 == 0:  # Only show every 3 hours
            hour_labels.append(f"{h}:00")
        else:
            hour_labels.append("")
    
    # Define time segments for better context (without emojis)
    time_segments = [
        {"name": "Nacht", "start": 0, "end": 6, "color": "#f8f8f8", 
         "symbol": "N", "desc": "Niedriger Verbrauch"},
        {"name": "Morgen", "start": 6, "end": 9, "color": "#fff8e1", 
         "symbol": "M", "desc": "Frühstück, Vorbereitung"},
        {"name": "Vormittag", "start": 9, "end": 12, "color": "#fffde7", 
         "symbol": "V", "desc": "Haushalt, Arbeit"},
        {"name": "Mittag", "start": 12, "end": 14, "color": "#fff8e1", 
         "symbol": "M", "desc": "Mittagessen, Kochen"},
        {"name": "Nachmittag", "start": 14, "end": 18, "color": "#fffde7", 
         "symbol": "N", "desc": "Arbeit, Freizeit"},
        {"name": "Abend", "start": 18, "end": 22, "color": "#fff8e1", 
         "symbol": "A", "desc": "Abendessen, Unterhaltung"},
        {"name": "Spätabend", "start": 22, "end": 24, "color": "#f8f8f8", 
         "symbol": "S", "desc": "Zur Ruhe kommen"}
    ]
    
    # Plot the activity bands at the bottom of the chart
    # First add background shading for time segments
    for segment in time_segments:
        ax_main.axvspan(segment["start"], segment["end"], 
                       alpha=0.15, color=segment["color"], zorder=0)
    
    # Plot data as stacked bar chart for better visual interpretation
    bar_width = 0.4
    x = np.arange(24)
    
    # Plot weekday data
    weekday_bars = ax_main.bar(x - bar_width/2, 
                             [heatmap_data['Werktag'][i] * np.max(df[df['Typ'] == 'Werktag'][column_name]) for i in range(24)], 
                             width=bar_width, label='Werktag', zorder=3)
    
    # Plot weekend data
    weekend_bars = ax_main.bar(x + bar_width/2, 
                             [heatmap_data['Wochenende'][i] * np.max(df[df['Typ'] == 'Wochenende'][column_name]) for i in range(24)], 
                             width=bar_width, label='Wochenende', zorder=3)
    
    # Color the bars based on consumption intensity with distinct color schemes
    for i, bar in enumerate(weekday_bars):
        bar.set_color(weekday_cmap(heatmap_data['Werktag'][i]))
        bar.set_edgecolor('#555555')
        bar.set_linewidth(0.5)
    
    for i, bar in enumerate(weekend_bars):
        bar.set_color(weekend_cmap(heatmap_data['Wochenende'][i]))
        bar.set_edgecolor('#555555')
        bar.set_linewidth(0.5)
    
    # Add segment names at the top of the chart instead of emojis
    for segment in time_segments:
        mid_point = (segment["start"] + segment["end"]) / 2
        # Add segment name 
        ax_main.text(mid_point, ax_main.get_ylim()[1] * 1.05, 
                   segment["name"], ha='center', fontsize=10, color='#333333')
    
    # Add grid lines at 6-hour intervals for better readability
    for hour in [6, 12, 18]:
        ax_main.axvline(hour, color='gray', linestyle='--', alpha=0.3, zorder=1)
    
    # Set axis labels and limits
    ax_main.set_xlabel("Tageszeit", fontsize=12)
    ax_main.set_ylabel("Stromverbrauch (kWh)", fontsize=12)
    ax_main.set_xlim(-0.5, 23.5)
    ax_main.set_xticks(range(0, 24, 3))
    ax_main.set_xticklabels([h for i, h in enumerate(hour_labels) if i % 3 == 0])
    
    # Ensure y-axis starts at 0
    ax_main.set_ylim(bottom=0)
    
    # Add legend with distinctive colors
    legend = ax_main.legend(loc='upper right', framealpha=0.9)
    legend.get_patches()[0].set_facecolor(weekday_cmap(0.7))  # Blue for weekday
    legend.get_patches()[1].set_facecolor(weekend_cmap(0.7))  # Orange for weekend
    
    # Add side panel content - practical interpretation
    ax_side.text(0.5, 0.95, "Was bedeutet das für Sie?", 
               ha='center', fontsize=14, fontweight='bold')
    
    # Re-normalize data for analysis (not display)
    normalized_weekday = heatmap_data['Werktag'] / np.max(heatmap_data['Werktag']) if np.max(heatmap_data['Werktag']) > 0 else np.zeros(24)
    normalized_weekend = heatmap_data['Wochenende'] / np.max(heatmap_data['Wochenende']) if np.max(heatmap_data['Wochenende']) > 0 else np.zeros(24)
    
    # Identify peak consumption time for weekdays
    weekday_peak_hour = np.argmax(heatmap_data['Werktag'])
    weekday_peak_segment = next((s for s in time_segments 
                               if s["start"] <= weekday_peak_hour < s["end"]), None)
    
    # Identify peak consumption time for weekends
    weekend_peak_hour = np.argmax(heatmap_data['Wochenende'])
    weekend_peak_segment = next((s for s in time_segments 
                               if s["start"] <= weekend_peak_hour < s["end"]), None)
    
    # Add insights box
    insight_text = (
        f"• Ihr Verbrauch ist am höchsten:\n"
        f"   Werktags: {weekday_peak_hour}:00 Uhr ({weekday_peak_segment['name']})\n"
        f"   Wochenende: {weekend_peak_hour}:00 Uhr ({weekend_peak_segment['name']})\n\n"
        f"• Deutliche Unterschiede zwischen\n   Werktag und Wochenende am:\n"
    )
    
    # Find hours with biggest weekday-weekend difference
    diff = np.abs(normalized_weekday - normalized_weekend)
    max_diff_hour = np.argmax(diff)
    max_diff_segment = next((s for s in time_segments 
                           if s["start"] <= max_diff_hour < s["end"]), None)
    
    insight_text += f"   - {max_diff_hour}:00 Uhr ({max_diff_segment['name']})\n"
    
    # Add second biggest difference if it's in a different segment
    diff[max_diff_hour] = 0  # Zero out the first max to find the second
    second_diff_hour = np.argmax(diff)
    second_diff_segment = next((s for s in time_segments 
                              if s["start"] <= second_diff_hour < s["end"]), None)
    
    if second_diff_segment and second_diff_segment["name"] != max_diff_segment["name"]:
        insight_text += f"   - {second_diff_hour}:00 Uhr ({second_diff_segment['name']})\n"
    
    # Add insights text box
    ax_side.text(0.05, 0.8, insight_text, fontsize=11, 
               va='top', ha='left', linespacing=1.5)
    
    # Add consumption pattern explanation
    pattern_title = "Tägliche Verbrauchsmuster:"
    ax_side.text(0.05, 0.4, pattern_title, fontsize=12, 
               fontweight='bold', va='top', ha='left')
    
    # Determine overall patterns
    morning_avg = np.mean([normalized_weekday[h] for h in range(6, 10)])
    midday_avg = np.mean([normalized_weekday[h] for h in range(10, 14)])
    evening_avg = np.mean([normalized_weekday[h] for h in range(18, 22)])
    
    # Create pattern descriptions
    pattern_text = ""
    if evening_avg > morning_avg * 1.5 and evening_avg > midday_avg * 1.5:
        pattern_text += "• Abend-Nutzer: Ihr Hauptverbrauch\n  findet abends statt.\n"
    elif morning_avg > evening_avg * 1.5 and morning_avg > midday_avg * 1.5:
        pattern_text += "• Morgen-Nutzer: Ihr Hauptverbrauch\n  findet morgens statt.\n"
    elif np.std([morning_avg, midday_avg, evening_avg]) < 0.1 * np.mean([morning_avg, midday_avg, evening_avg]):
        pattern_text += "• Gleichmäßiger Nutzer: Ihr Verbrauch\n  ist über den Tag verteilt.\n"
    else:
        pattern_text += "• Gemischtes Profil: Mehrere\n  Verbrauchsspitzen über den Tag.\n"
    
    ax_side.text(0.05, 0.35, pattern_text, fontsize=11, 
               va='top', ha='left', linespacing=1.5)
    
    # Add color legends for both day types
    # Weekday color bar
    color_bar_y_weekday = 0.15
    color_bar_height = 0.03
    color_bar_width = 0.7
    
    for i in range(100):
        ax_side.add_patch(
            patches.Rectangle(
                (0.15 + i * color_bar_width/100, color_bar_y_weekday),
                color_bar_width/100, color_bar_height,
                facecolor=weekday_cmap(i/100),
                edgecolor="none"
            )
        )
    
    ax_side.text(0.1, color_bar_y_weekday, "Werktag:", fontsize=10, ha='right', va='center')
    ax_side.text(0.15, color_bar_y_weekday - 0.02, "Niedrig", fontsize=9, ha='left', va='top')
    ax_side.text(0.15 + color_bar_width, color_bar_y_weekday - 0.02, "Hoch", fontsize=9, ha='right', va='top')
    
    # Weekend color bar
    color_bar_y_weekend = 0.08
    
    for i in range(100):
        ax_side.add_patch(
            patches.Rectangle(
                (0.15 + i * color_bar_width/100, color_bar_y_weekend),
                color_bar_width/100, color_bar_height,
                facecolor=weekend_cmap(i/100),
                edgecolor="none"
            )
        )
    
    ax_side.text(0.1, color_bar_y_weekend, "Wochenende:", fontsize=10, ha='right', va='center')
    ax_side.text(0.15, color_bar_y_weekend - 0.02, "Niedrig", fontsize=9, ha='left', va='top')
    ax_side.text(0.15 + color_bar_width, color_bar_y_weekend - 0.02, "Hoch", fontsize=9, ha='right', va='top')
    
    # Add title and subtitle
    fig.suptitle("Ihr tägliches Stromverbrauchsprofil", fontsize=16, fontweight='bold', y=0.98)
    plt.figtext(0.5, 0.94, f"{start.strftime('%d.%m.%Y')} bis {end.strftime('%d.%m.%Y')}", 
              ha="center", fontsize=12)
    
    plt.tight_layout(rect=[0, 0, 1, 0.92])
    plt.subplots_adjust(wspace=0.05)
    plt.savefig(column_name+"barplots.svg")
    #plt.show()