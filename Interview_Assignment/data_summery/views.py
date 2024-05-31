import pandas as pd
from django.shortcuts import render
from django.http import HttpResponseRedirect
from .form import UploadFileForm
import plotly.graph_objects as go
import io
import base64


def handle_uploaded_file(f):
    # Process the uploaded file
    #cheack the file type
    if f.name.endswith('.csv'):
        df = pd.read_csv(f)
    elif f.name.endswith('.xlsx'):
        df = pd.read_excel(f)
    else:
        return 'Invalid file type'
    
    #check the columns
    if 'Cust State' not in df.columns or 'DPD' not in df.columns:
        return 'Invalid columns'
    
    #summary of the data
    summary = pd.DataFrame(columns=['No.','State', 'DPD', 'Count'])
    summary['State'] = df['Cust State'].unique()

    for state in summary['State']:
        state_data = df[df['Cust State'] == state]
        summary.loc[summary['State'] == state, 'DPD'] = state_data['DPD'].sum()
        summary.loc[summary['State'] == state, 'Count'] = state_data.shape[0]
    summary['No.'] = summary.index + 1
    return summary

def pie_plot_to_base64(summary, title='State wise DPD count'):
    # Sort the summary DataFrame by DPD in descending order
    summary_sorted = summary.sort_values(by='DPD', ascending=False)

    # Get top 5 states and their DPD counts
    top_5_states = summary_sorted.head(7)
    top_5_states_total = top_5_states['DPD'].sum()

    # Aggregate DPD counts for the rest of the states
    other_states_total = summary_sorted.iloc[7:]['DPD'].sum()

    # Combine top 5 states and "Other"
    combined_data = pd.concat([top_5_states, pd.DataFrame({'State': ['Other'], 'DPD': [other_states_total]})])

    # Generate the plot with Plotly
    fig = go.Figure(data=[go.Pie(labels=combined_data['State'], values=combined_data['DPD'], hole=0.3)])

    # Update layout
    fig.update_layout(title=title)

    # Convert plot to SVG and encode it to base64
    img = io.BytesIO()
    fig.write_image(img, format='svg')
    img.seek(0)
    plot_base64 = base64.b64encode(img.getvalue()).decode()

    return plot_base64

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            summary = handle_uploaded_file(request.FILES['file'])
            plot_base64 = pie_plot_to_base64(summary, title='State wise DPD count')
            return render(request, 'summary.html', {'summary': summary.to_html(index=False), 'plot_base64': plot_base64})
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})

    
