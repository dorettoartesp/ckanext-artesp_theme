(function (window, ckan, ckanJQuery) {
  if (!ckan || !ckan.module || !ckan.module.registry || !ckanJQuery) {
    return;
  }

  var Autocomplete = ckan.module.registry.autocomplete;

  if (!Autocomplete || !Autocomplete.prototype || Autocomplete.prototype._artespAutocompletePatched) {
    return;
  }

  function patchMethod(name) {
    var original = Autocomplete.prototype[name];
    var source;
    var patchedSource;
    var patched;

    if (typeof original !== 'function') {
      return;
    }

    source = Function.prototype.toString.call(original);
    patchedSource = source
      .replace(/\$\.fn/g, 'jQuery.fn')
      .replace(/\$\(/g, 'jQuery(');

    if (patchedSource === source) {
      return;
    }

    try {
      patched = new Function('jQuery', 'return (' + patchedSource + ');')(ckanJQuery);
    } catch (error) {
      return;
    }

    Autocomplete.prototype[name] = patched;
  }

  patchMethod('setupAutoComplete');
  patchMethod('lookup');
  patchMethod('formatResult');
  patchMethod('templateResult');

  Autocomplete.prototype._artespAutocompletePatched = true;
})(window, window.ckan, window.jQuery);
