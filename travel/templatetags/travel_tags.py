from django.conf import settings
from django import template

try:
    import ipdb as pdb
except ImportError:
    import pdb


register = template.Library()

#===============================================================================
class HavingNode(template.Node):
    
    #---------------------------------------------------------------------------
    def __init__(self, having_var, context_var, nodelist, nodelist_else):
        self.having_var = having_var
        self.context_var = context_var
        self.nodelist = nodelist
        self.nodelist_else = nodelist_else
    
    #---------------------------------------------------------------------------
    def render(self, context):
        value = self.having_var.resolve(context)
        if value:
            with context.push(**{self.context_var: value}):
                return self.nodelist.render(context)

        if self.nodelist_else:
            return self.nodelist_else.render(context)
            
        return ''


#-------------------------------------------------------------------------------
@register.tag('having')
def do_having(parser, token):
    having_err_msg = "'having' statements should use the format 'having x as y': '{}'"
    bits = token.split_contents()
    if len(bits) < 4:
        raise template.TemplateSyntaxError(having_err_msg.format(token.contents))

    tag_name, having_var, _as, context_var = bits
    having_var = parser.compile_filter(having_var)
    if _as != 'as':
        raise template.TemplateSyntaxError(having_err_msg.format(token.contents))

    nodelist = parser.parse(('else', 'endhaving',))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_else = parser.parse(('endhaving',))
        parser.delete_first_token()
    else:
        nodelist_else = None
        
    return HavingNode(having_var, context_var, nodelist, nodelist_else)


#===============================================================================
class SetTraceNode(template.Node):
    '''
    Adapted from http://www.djangosnippets.org/snippets/1550/
    '''
    
    #---------------------------------------------------------------------------
    def render(self, context):
        return pdb.set_trace() or ''


#-------------------------------------------------------------------------------
@register.tag('set_trace')
def do_set_trace(parser, token):
    '''
    Tag that inspects template context.

    Usage: 
    {% set_trace %}
    '''
    return SetTraceNode()
