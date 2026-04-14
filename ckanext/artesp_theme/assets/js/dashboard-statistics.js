(function() {
  function ready(callback) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', callback);
      return;
    }
    callback();
  }

  function setText(root, selector, value) {
    const element = root.querySelector(selector);
    if (element) {
      element.textContent = value;
    }
  }

  function renderBarList(items, label, emptyMessage) {
    if (!items || !items.length) {
      const empty = document.createElement('p');
      empty.className = 'dashboard-statistics__empty';
      empty.textContent = emptyMessage;
      return empty;
    }

    const list = document.createElement('ol');
    list.className = 'dashboard-statistics__bar-list';
    list.setAttribute('aria-label', label);

    items.forEach(function(item) {
      const row = document.createElement('li');
      row.className = 'dashboard-statistics__bar-item';

      const heading = document.createElement('div');
      heading.className = 'dashboard-statistics__bar-label';

      const name = document.createElement('span');
      name.textContent = item.label;

      const value = document.createElement('strong');
      value.textContent = item.value;

      const track = document.createElement('div');
      track.className = 'dashboard-statistics__bar-track';
      track.setAttribute('aria-hidden', 'true');

      const bar = document.createElement('span');
      bar.style.width = Math.max(0, Math.min(100, item.percent || 0)) + '%';

      heading.appendChild(name);
      heading.appendChild(value);
      track.appendChild(bar);
      row.appendChild(heading);
      row.appendChild(track);
      list.appendChild(row);
    });

    return list;
  }

  function replaceChart(root, name, items) {
    const target = root.querySelector('[data-dashboard-chart="' + name + '"]');
    if (!target) {
      return;
    }

    const labels = {
      timeline: 'Evolução temporal das publicações',
      resources_by_theme: 'Recursos por tema',
      datasets_by_theme: 'Conjuntos por tema',
      top_datasets: 'Conjuntos com maior volume de recursos',
      formats: 'Formatos de publicação'
    };
    const emptyMessages = {
      timeline: 'Ainda não há séries temporais suficientes para exibição.',
      resources_by_theme: 'Ainda não há recursos suficientes para distribuição temática.',
      datasets_by_theme: 'Ainda não há conjuntos suficientes para distribuição temática.',
      top_datasets: 'Ainda não há recursos suficientes para compor o ranking.',
      formats: 'Ainda não há formatos suficientes para consolidação.'
    };

    target.replaceChildren(
      renderBarList(items, labels[name], emptyMessages[name])
    );
  }

  function renderInsights(root, insights) {
    const target = root.querySelector('[data-dashboard-insights]');
    if (!target) {
      return;
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'dashboard-statistics__insights';

    (insights || []).forEach(function(insight) {
      const item = document.createElement('div');
      item.className = 'dashboard-statistics__insight';

      const title = document.createElement('strong');
      title.textContent = insight.title;

      const description = document.createElement('span');
      description.textContent = insight.description;

      item.appendChild(title);
      item.appendChild(description);
      wrapper.appendChild(item);
    });

    target.replaceChildren(wrapper);
  }

  function renderTable(root, rows) {
    const body = root.querySelector('[data-dashboard-table-body]');
    if (!body) {
      return;
    }

    if (!rows || !rows.length) {
      const row = document.createElement('tr');
      const cell = document.createElement('td');
      cell.colSpan = 5;
      cell.textContent = 'Ainda não há conjuntos públicos suficientes para compor a tabela.';
      row.appendChild(cell);
      body.replaceChildren(row);
      return;
    }

    const renderedRows = rows.map(function(item) {
      const row = document.createElement('tr');
      const rank = document.createElement('td');
      const dataset = document.createElement('td');
      const theme = document.createElement('td');
      const resources = document.createElement('td');
      const share = document.createElement('td');
      const link = document.createElement('a');
      const meta = document.createElement('span');
      const badge = document.createElement('span');
      const shareWrapper = document.createElement('div');
      const shareBar = document.createElement('div');
      const shareFill = document.createElement('span');
      const shareLabel = document.createElement('span');

      rank.textContent = item.rank;
      link.className = 'dashboard-statistics__dataset-link';
      link.href = '/dataset/' + encodeURIComponent(item.name);
      link.textContent = item.title;
      meta.className = 'dashboard-statistics__dataset-meta';
      meta.textContent = item.formats_label + ' · atualizado em ' + item.modified_label;
      dataset.appendChild(link);
      dataset.appendChild(meta);

      badge.className = 'dashboard-statistics__badge';
      badge.textContent = item.theme;
      theme.appendChild(badge);
      resources.textContent = item.resource_count;

      shareWrapper.className = 'dashboard-statistics__share';
      shareBar.className = 'dashboard-statistics__share-bar';
      shareFill.style.width = Math.max(0, Math.min(100, item.share_percent || 0)) + '%';
      shareLabel.textContent = item.share_label + '%';
      shareBar.appendChild(shareFill);
      shareWrapper.appendChild(shareBar);
      shareWrapper.appendChild(shareLabel);
      share.appendChild(shareWrapper);

      row.appendChild(rank);
      row.appendChild(dataset);
      row.appendChild(theme);
      row.appendChild(resources);
      row.appendChild(share);
      return row;
    });

    body.replaceChildren.apply(body, renderedRows);
  }

  function updateDashboard(root, payload) {
    Object.keys(payload.kpis || {}).forEach(function(key) {
      const metric = root.querySelector('[data-dashboard-metric="' + key + '"]');
      if (metric) {
        metric.textContent = payload.kpis[key];
      }
    });

    renderInsights(root, payload.insights);
    replaceChart(root, 'timeline', payload.charts.timeline);
    replaceChart(root, 'resources_by_theme', payload.charts.resources_by_theme);
    replaceChart(root, 'datasets_by_theme', payload.charts.datasets_by_theme);
    replaceChart(root, 'top_datasets', payload.charts.top_datasets);
    replaceChart(root, 'formats', payload.charts.formats);
    renderTable(root, payload.table_rows);
    setText(root, '[data-dashboard-table-total]', payload.table_total_count);
    setText(
      root,
      '[data-dashboard-status]',
      'Painel atualizado: ' + payload.filters.theme_label + ' em ' + payload.filters.period_label.toLowerCase() + '.'
    );
  }

  function setLoading(root, isLoading) {
    root.toggleAttribute('data-dashboard-loading', isLoading);
    const button = root.querySelector('.dashboard-statistics__filter-submit');
    if (button) {
      button.disabled = isLoading;
      button.textContent = isLoading ? 'Atualizando...' : 'Atualizar painel';
    }
  }

  ready(function() {
    const root = document.querySelector('[data-dashboard-root]');
    if (!root || !window.fetch) {
      return;
    }

    const form = root.querySelector('[data-dashboard-filter-form]');
    if (!form) {
      return;
    }

    form.addEventListener('submit', function(event) {
      event.preventDefault();

      const params = new URLSearchParams(new FormData(form));
      const endpoint = root.getAttribute('data-dashboard-endpoint');
      setLoading(root, true);
      setText(root, '[data-dashboard-status]', 'Atualizando painel...');

      fetch(endpoint + '?' + params.toString(), {
        headers: {Accept: 'application/json'}
      })
        .then(function(response) {
          if (!response.ok) {
            throw new Error('Falha ao carregar estatísticas.');
          }
          return response.json();
        })
        .then(function(body) {
          if (!body.success) {
            throw new Error('A API retornou erro ao carregar estatísticas.');
          }
          updateDashboard(root, body.result);
          window.history.replaceState(null, '', form.action + '?' + params.toString());
        })
        .catch(function() {
          setText(
            root,
            '[data-dashboard-status]',
            'Não foi possível atualizar o painel. Recarregue a página ou tente novamente.'
          );
        })
        .finally(function() {
          setLoading(root, false);
        });
    });
  });
}());
