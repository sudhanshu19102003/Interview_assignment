import pandas as pd
from django.shortcuts import render
from .form import UploadFileForm
import plotly.graph_objects as go
import io
import base64
import time

class InvalidFileTypeError(Exception):
    pass

class InvalidColumnsError(Exception):
    pass

def handle_uploaded_file(f):
    # Process the uploaded file
    try:
        # Check the file type
        if f.name.endswith('.csv'):
            df = pd.read_csv(f)
        elif f.name.endswith('.xlsx'):
            df = pd.read_excel(f)
        else:
            raise InvalidFileTypeError("Invalid file type. Please upload a .csv or .xlsx file.")
        
        # Check the columns
        required_columns = {'Cust State', 'DPD'}
        if not required_columns.issubset(df.columns):
            raise InvalidColumnsError("Invalid columns. Required columns: Cust State and DPD.")
        
        # Summary of the data
        summary = pd.DataFrame(columns=['No.', 'State', 'DPD', 'Count'])
        summary['State'] = df['Cust State'].unique()
        
        for state in summary['State']:
            state_data = df[df['Cust State'] == state]
            summary.loc[summary['State'] == state, 'DPD'] = state_data['DPD'].sum()
            summary.loc[summary['State'] == state, 'Count'] = state_data.shape[0]
        summary['No.'] = summary.index + 1
        return summary
    except InvalidFileTypeError as e:
        return str(e)
    except InvalidColumnsError as e:
        return str(e)
    except Exception as e:
        return f"An error occurred while processing the file: {str(e)}"

def pie_plot_to_base64(summary, title='State wise DPD count'):
    # Sort the summary DataFrame by DPD in descending order
    summary_sorted = summary.sort_values(by='DPD', ascending=False)

    # Get top 5 states and their DPD counts
    top_5_states = summary_sorted.head(7)
    
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
            result = handle_uploaded_file(request.FILES['file'])
            if isinstance(result, pd.DataFrame):
                summary = result
                plot_base64 = pie_plot_to_base64(summary, title='State wise DPD count')
                return render(request, 'summary.html', {'summary': summary.to_html(index=False), 'plot_base64': plot_base64})
            else:
                # result contains an error message
                return render(request, 'upload.html', {'form': form, 'error': result})
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})

