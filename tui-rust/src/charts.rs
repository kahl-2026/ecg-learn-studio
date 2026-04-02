// Chart rendering utilities for ECG signals

use ratatui::{
    style::{Color, Style},
    symbols,
    text::Span,
    widgets::{Axis, Block, Borders, Chart, Dataset, GraphType},
};

#[allow(dead_code)]
pub struct ECGChart {
    pub data: Vec<(f64, f64)>,
    pub title: String,
}

#[allow(dead_code)]
impl ECGChart {
    pub fn new(signal: &[f64], title: String) -> Self {
        let data: Vec<(f64, f64)> = signal
            .iter()
            .enumerate()
            .map(|(i, &val)| (i as f64, val))
            .collect();

        Self { data, title }
    }

    pub fn render<'a>(&'a self) -> Chart<'a> {
        let dataset = Dataset::default()
            .name("ECG Signal")
            .marker(symbols::Marker::Braille)
            .graph_type(GraphType::Line)
            .style(Style::default().fg(Color::Cyan))
            .data(&self.data);

        let x_max = self.data.len() as f64;
        let y_min = self.data.iter().map(|(_, y)| y).fold(f64::INFINITY, |a, &b| a.min(b));
        let y_max = self.data.iter().map(|(_, y)| y).fold(f64::NEG_INFINITY, |a, &b| a.max(b));

        Chart::new(vec![dataset])
            .block(Block::default().title(self.title.clone()).borders(Borders::ALL))
            .x_axis(
                Axis::default()
                    .title("Time (samples)")
                    .bounds([0.0, x_max])
                    .labels(vec![
                        Span::raw("0"),
                        Span::raw(format!("{:.0}", x_max / 2.0)),
                        Span::raw(format!("{:.0}", x_max)),
                    ]),
            )
            .y_axis(
                Axis::default()
                    .title("Amplitude")
                    .bounds([y_min, y_max])
                    .labels(vec![
                        Span::raw(format!("{:.2}", y_min)),
                        Span::raw(format!("{:.2}", (y_min + y_max) / 2.0)),
                        Span::raw(format!("{:.2}", y_max)),
                    ]),
            )
    }
}
