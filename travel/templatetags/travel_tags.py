from django.conf import settings
from django import template

register = template.Library()

#-------------------------------------------------------------------------------
@register.inclusion_tag('visit-this.html')
def visit_this():
    return dict()


#===============================================================================
class RenderNode(template.Node):
    
    #---------------------------------------------------------------------------
    def __init__(self, tmpl):
        self.tmpl = template.Variable(tmpl)

    #---------------------------------------------------------------------------
    def render(self, context):
        try:
            tmpl = self.tmpl.resolve(context)
            return tmpl.render(context)
        except template.TemplateSyntaxError, e:
            if settings.TEMPLATE_DEBUG:
                raise
            return ''
        except:
            return '' # Fail silently for invalid included templates.

#-------------------------------------------------------------------------------
@register.tag('render')
def do_render(parser, token):
    """
    Loads a template and renders it with the current context.

    Example::

        {% include "foo/some_include" %}
    """
    bits = token.contents.split()
    if len(bits) != 2:
        raise template.TemplateSyntaxError(
            "%r tag takes one argument: the template to be rendered" % bits[0]
        )
        
    path = bits[1]
    # if path[0] in ('"', "'") and path[-1] == path[0]:
    #     return ConstantIncludeNode(path[1:-1])
    return RenderNode(bits[1])
    
