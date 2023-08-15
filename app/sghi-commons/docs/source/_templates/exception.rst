{{ fullname | escape | underline}}

.. currentmodule:: {{ module }}

.. autoexception:: {{ objname }}
   :members:
   :show-inheritance:
   :inherited-members:
   :member-order: groupwise

   {% if methods or attributes %}
   ----
   {% endif %}

   {% block methods %}
   {% if methods %}
   .. rubric:: {{ _('Methods') }}

   .. autosummary::
   {% for item in methods %}
      ~{{ name }}.{{ item }}
   {%- endfor %}

   {% endif %}
   {% endblock %}

   {% block attributes %}
   {% if attributes %}
   .. rubric:: {{ _('Attributes') }}

   .. autosummary::
   {% for item in attributes %}
      ~{{ name }}.{{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% if methods or attributes %}
   ----
   {% endif %}

   {% block constructor %}
   .. automethod:: __init__
   {% endblock %}
