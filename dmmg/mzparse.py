# import sys
import ply.yacc as yacc
# Get the token map from the lexer.  This is required.
from mzlex import tokens

from distances import lcs_vector, lcs_print


class Node:
    def __init__(self, typ, leafs, children, prod):
        self.typ = typ
        self.leafs = leafs
        self.children = children
        self.prod = prod

    def __str__(self):
        ch_string = ''
        leaf_string = ''
        for leaf in self.leafs:
            leaf_string += self.prod[leaf - 1].__str__()
        for child in self.children:
            ch_string += self.prod[child - 1].typ
        return '(%s: %s %s)' % (self.typ, leaf_string, ch_string)

    def dump_tree(self):
        ch_string = ''
        leaf_string = ''
        for leaf in self.leafs:
            leaf_string += self.prod[leaf - 1].__str__()
        for child in self.children:
            ch_string += self.prod[child - 1].dump_tree()
        return '(%s: %s %s)' % (self.typ, leaf_string, ch_string)

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        if self.typ == other.typ:
            if len(self.prod) == len(other.prod):
                for i in xrange(len(self.prod)):
                    if (type(self.prod[i]) == str and
                        type(other.prod[i]) == str):
                        if self.prod[i] != other.prod[i]:
                            return False
                return True
            else:
                return False
        else:
            return False

    def dump_tree_terminals(self):
        """Return a string containing the terminals producted by the grammar
        that has generated this tree."""
        ch_string = ''
        for p in self.prod:
            if type(p) == str:
                ch_string += (p + ' ')
            else:
                ch_string += p.dump_tree_terminals()
        return '%s' % (ch_string)

    def dump_subtree_terminals(self, lev):
        """Return a string containing the terminals producted by the grammar
        that has generated this tree. The lev parameter specify when to stop"""
        ch_string = ''
        lev -= 1
        for p in self.prod:
            if type(p) == str:
                ch_string += (p + ' ')
            else:
                if lev == 0:
                    ch_string += (p.typ + ' ')
                else:
                    temp_ch_string, lev = p.dump_subtree_terminals(lev)
                    ch_string += temp_ch_string
        return (ch_string, lev)

    def create_tree_vector(self):
        """Return a vector containing nodes in a dfs order"""
        tree_vector = [self]
        for child in self.children:
            tree_vector.extend(self.prod[child - 1].create_tree_vector())
        return tree_vector


## ITEMS ##

def p_model(p):
    """model : epsilon
             | item ';' model"""
    if len(p) == 4:
        p[0] = Node('model', [2], [1, 3], p[1:])
    else:
        p[0] = Node('model', [], [1], p[1:])


def p_item(p):
    """item : type_inst_syn_item
            | enum_item
            | include_item
            | var_decl_item
            | assign_item
            | constraint_item
            | solve_item
            | output_item
            | predicate_item
            | test_item
            | function_item
            | annotation_item"""
    p[0] = Node('item', [], [1], p[1:])


def p_type_inst_syn_item(p):
    """type_inst_syn_item : TYPE IDENT annotations '=' ti_expr"""
    p[0] = Node('type_inst_syn_item', [1, 2, 4], [3, 5], p[1:])


def p_enum_item(p):
    """enum_item : ENUM IDENT annotations
                 | ENUM IDENT annotations '=' enum_cases"""
    if len(p) == 4:
        p[0] = Node('enum_item', [1, 2], [3], p[1:])
    else:
        p[0] = Node('enum_item', [1, 2, 4], [3, 5], p[1:])


def p_enum_cases(p):
    """enum_cases     : '{' enum_case enum_case_star '}'
       enum_case_star : epsilon
                      | ',' enum_case enum_case_star"""
    if len(p) == 5:
        p[0] = Node('enum_cases', [1, 4], [2, 3], p[1:])
    elif len(p) == 4:
        p[0] = Node('enum_case_star', [1], [2, 3], p[1:])
    else:
        p[0] = Node('enum_case_star', [], [1], p[1:])


def p_enum_case(p):
    """enum_case : IDENT
                 | IDENT '(' ti_expr_and_id ti_expr_and_id_star ')'"""
    if len(p) == 6:
        p[0] = Node('enum_case', [1, 2, 5], [3, 4], p[1:])
    else:
        p[0] = Node('enum_case', [1], [], p[1:])


def p_ti_expr_and_id(p):
    """ti_expr_and_id : ti_expr ':' IDENT"""
    p[0] = Node('ti_expr_and_id', [2, 3], [1], p[1:])


def p_include_item(p):
    """include_item : INCLUDE string_literal"""
    p[0] = Node('include_item', [1], [2], p[1:])


def p_var_decl_item(p):
    """var_decl_item : ti_expr_and_id annotations
                     | ti_expr_and_id annotations '=' expr"""
    if len(p) == 3:
        p[0] = Node('var_decl_item', [], [1, 2], p[1:])
    else:
        p[0] = Node('var_decl_item', [3], [1, 2, 4], p[1:])


def p_assign_item(p):
    """assign_item : IDENT '=' expr"""
    p[0] = Node('assign_item', [1, 2], [3], p[1:])


def p_constraint_item(p):
    """constraint_item : CONSTRAINT expr"""
    p[0] = Node('constraint_item', [1], [2], p[1:])


def p_solve_item(p):
    """solve_item : SOLVE annotations SATISFY
                  | SOLVE annotations MINIMIZE expr
                  | SOLVE annotations MAXIMIZE expr"""
    if len(p) == 4:
        p[0] = Node('solve_item', [1, 3], [2], p[1:])
    else:
        p[0] = Node('solve_item', [1, 3], [2, 4], p[1:])


def p_output_item(p):
    """output_item : OUTPUT expr"""
    p[0] = Node('output_item', [1], [2], p[1:])


def p_annotation_item(p):
    """annotation_item : ANNOTATION IDENT params"""
    p[0] = Node('annotation_item', [1, 2], [3], p[1:])


def p_predicate_item(p):
    """predicate_item : PREDICATE operation_item_tail"""
    p[0] = Node('predicate_item', [1], [2], p[1:])


def p_test_item(p):
    """test_item : TEST operation_item_tail"""
    p[0] = Node('test_item', [1], [2], p[1:])


def p_function_item(p):
    """function_item : FUNCTION ti_expr ':' operation_item_tail"""
    p[0] = Node('function_item', [1, 3], [2, 4], p[1:])


def p_operation_item_tail(p):
    """operation_item_tail : IDENT params annotations
                           | IDENT params annotations '=' expr"""
    if len(p) == 4:
        p[0] = Node('operation_item_tail', [1], [2, 3], p[1:])
    else:
        p[0] = Node('operation_item_tail', [1, 4], [2, 3, 5], p[1:])


def p_params(p):
    """params : epsilon
              | '(' ti_expr_and_id ti_expr_and_id_star ')'"""
    if len(p) == 5:
        p[0] = Node('params', [1, 4], [2, 3], p[1:])
    else:
        p[0] = Node('params', [], [1], p[1:])


## TYPE-INST-EXPRESSIONS ##

def p_ti_expr(p):
    """ti_expr : '(' ti_expr ':' IDENT WHERE expr ')'
               | base_ti_expr"""
    if len(p) == 8:
        p[0] = Node('ti_expr', [1, 3, 4, 5, 7], [2, 6], p[1:])
    else:
        p[0] = Node('ti_expr', [], [1], p[1:])


def p_base_ti_expr(p):
    """base_ti_expr : var_par base_ti_expr_tail"""
    p[0] = Node('base_ti_expr', [], [1, 2], p[1:])


def p_var_par(p):
    """var_par : epsilon
               | PAR
               | VAR"""
    if type(p[1]) is str:
        p[0] = Node('var_par', [1], [], p[1:])
    else:
        p[0] = Node('var_par', [], [1], p[1:])


def p_base_ti_expr_tail(p):
    """base_ti_expr_tail : IDENT
                         | BOOL
                         | INT
                         | FLOAT
                         | STRING
                         | set_ti_expr_tail
                         | array_ti_expr_tail
                         | tuple_ti_expr_tail
                         | record_ti_expr_tail
                         | ti_variable_expr_tail
                         | ANN
                         | op_ti_expr_tail
                         | '{' expr expr_star '}'
                         | num_expr DOTS num_expr"""
    if len(p) == 5:
        p[0] = Node('base_ti_expr_tail', [1, 4], [2, 3], p[1:])
    elif len(p) == 4:
        p[0] = Node('base_ti_expr_tail', [2], [1, 3], p[1:])
    elif (p[1] == 'ident' or
          p[1] == 'bool' or
          p[1] == 'int' or
          p[1] == 'float' or
          p[1] == 'string' or
          p[1] == 'ann'):
        p[0] = Node('base_ti_expr_tail', [1], [], p[1:])
    else:
        p[0] = Node('base_ti_expr_tail', [], [1], p[1:])


def p_set_ti_expr_tail(p):
    """set_ti_expr_tail : SET OF ti_expr"""
    p[0] = Node('set_ti_expr_tail', [1, 2], [3], p[1:])


def p_array_ti_expr_tail(p):
    """array_ti_expr_tail : ARRAY '[' ti_expr ti_expr_star ']' OF ti_expr
                          | LIST OF ti_expr"""
    if len(p) == 8:
        p[0] = Node('array_ti_expr_tail', [1, 2, 5, 6], [3, 4, 7], p[1:])
    else:
        p[0] = Node('array_ti_expr_tail', [1, 2], [3], p[1:])


def p_tuple_ti_expr_tail(p):
    """tuple_ti_expr_tail : TUPLE '(' ti_expr ti_expr_star ')'"""
    p[0] = Node('tuple_ti_expr_tail', [1, 2, 5], [3, 4], p[1:])


def p_record_ti_exprtail(p):
    """record_ti_expr_tail  : RECORD '(' ti_expr_and_id ti_expr_and_id_star ')'"""
    p[0] = Node('record_ti_expr_tail', [1, 2, 5], [3, 4], p[1:])


def p_ti_variable_expr_tail(p):
    """ti_variable_expr_tail : IDENT
                             | ANY IDENT"""
    if len(p) == 2:
        p[0] = Node('ti_variable_expr_tail', [1], [], p[1:])
    else:
        p[0] = Node('ti_variable_expr_tail', [1, 2], [], p[1:])


def p_op_ti_expr_tail(p):
    """op_ti_expr_tail : OP '(' ti_expr ':' '(' ti_expr ti_expr_star ')' ')'"""
    p[0] = Node('op_ti_expr_tail', [1, 2, 4, 5, 8, 9], [3, 6, 7], p[1:])


## EXPRESSIONS ##

def p_expr(p):
    """expr : expr_atom expr_binop_tail"""
    p[0] = Node('expr', [], [1, 2], p[1:])


def p_expr_atom(p):
    """expr_atom : expr_atom_head expr_atom_tail annotations"""
    p[0] = Node('expr_atom', [], [1, 2, 3], p[1:])


def p_expr_binop_tail(p):
    """expr_binop_tail : epsilon
                       | bin_op expr"""
    if len(p) == 2:
        p[0] = Node('expr_binop_tail', [], [1], p[1:])
    else:
        p[0] = Node('expr_binop_tail', [], [1, 2], p[1:])


def p_expr_atom_head(p):
    """expr_atom_head : builtin_un_op expr_atom
                      | '(' expr ')'
                      | ident_or_quoted_op
                      | '_'
                      | bool_literal
                      | int_literal
                      | float_literal
                      | string_literal
                      | set_literal
                      | set_comp
                      | simple_array_literal
                      | simple_array_literal_2d
                      | indexed_array_literal
                      | simple_array_comp
                      | indexed_array_comp
                      | tuple_literal
                      | record_literal
                      | enum_literal
                      | ann_literal
                      | if_then_else_expr
                      | case_expr
                      | let_expr
                      | call_expr
                      | gen_call_expr"""
    if len(p) == 2 and p[1] == '_':
        p[0] = Node('expr_atom_head', [1], [], p[1:])
    elif len(p) == 3:
        p[0] = Node('expr_atom_head', [], [1, 2], p[1:])
    elif len(p) == 4:
        p[0] = Node('expr_atom_head', [1, 3], [2], p[1:])
    else:
        p[0] = Node('expr_atom_head', [], [1], p[1:])


def p_expr_atom_tail(p):
    """expr_atom_tail : epsilon
                      | array_access_tail expr_atom_tail
                      | tuple_access_tail expr_atom_tail
                      | record_access_tail expr_atom_tail"""
    if len(p) == 2:
        p[0] = Node('expr_atom_tail', [], [1], p[1:])
    else:
        p[0] = Node('expr_atom_tail', [], [1, 2], p[1:])


def p_num_expr(p):
    """num_expr : num_expr_atom num_expr_binop_tail"""
    p[0] = Node('num_expr', [], [1, 2], p[1:])


def p_num_expr_atom(p):
    """num_expr_atom : num_expr_atom_head expr_atom_tail annotations"""
    p[0] = Node('num_expr_atom', [], [1, 2, 3], p[1:])


def p_num_expr_binop_tail(p):
    """num_expr_binop_tail : epsilon
                           | num_bin_op num_expr"""
    if len(p) == 2:
        p[0] = Node('num_expr_binop_tail', [], [1], p[1:])
    else:
        p[0] = Node('num_expr_binop_tail', [], [1, 2], p[1:])


def p_num_expr_atom_head(p):
    """num_expr_atom_head : builtin_num_un_op num_expr_atom
                          | '(' num_expr ')'
                          | ident_or_quoted_op
                          | int_literal
                          | float_literal
                          | if_then_else_expr
                          | case_expr
                          | let_expr
                          | call_expr
                          | gen_call_expr"""
    if len(p) == 2:
        p[0] = Node('num_expr_atom_head', [], [1], p[1:])
    elif len(p) == 3:
        p[0] = Node('num_expr_atom_head', [], [1, 2], p[1:])
    else:
        p[0] = Node('num_expr_atom_head', [1, 3], [2], p[1:])


def p_builtin_op(p):
    """builtin_op : builtin_bin_op
                  | builtin_un_op"""
    p[0] = Node('builtin_op', [], [1], p[1:])


def p_bin_op(p):
    """bin_op : builtin_bin_op
              | QUOT IDENT QUOT"""
    if len(p) == 4:
        p[0] = Node('bin_op', [1, 2, 3], [], p[1:])
    else:
        p[0] = Node('bin_op', [], [1], p[1:])


def p_builtin_bin_op(p):
    """builtin_bin_op : IFF
                      | SUF
                      | NEC
                      | DIS
                      | XOR
                      | CON
                      | '<'
                      | '>'
                      | LEQ
                      | GEQ
                      | EQ
                      | '='
                      | DIF
                      | IN
                      | SUBSET
                      | SUPERSET
                      | UNION
                      | DIFF
                      | SYMDIFF
                      | DOTS
                      | INTERSECT
                      | PP
                      | builtin_num_bin_op"""
    if type(p[1]) is str:
        p[0] = Node('builtin_bin_op', [1], [], p[1:])
    else:
        p[0] = Node('builtin_bin_op', [], [1], p[1:])


def p_builtin_un_op(p):
    """builtin_un_op : NOT
                     | builtin_num_un_op"""
    if p[1] == 'not':
        p[0] = Node('builtin_un_op', [1], [], p[1:])
    else:
        p[0] = Node('builtin_un_op', [], [1], p[1:])


def p_num_bin_op(p):
    """num_bin_op : builtin_num_bin_op
                  | QUOT IDENT QUOT"""
    if len(p) == 2:
        p[0] = Node('num_bin_op', [], [1], p[1:])
    else:
        p[0] = Node('num_bin_op', [1, 2, 3], [], p[1:])


def p_builtin_num_bin_op(p):
    """builtin_num_bin_op : '+'
                          | '-'
                          | '*'
                          | '/'
                          | DIV
                          | MOD"""
    p[0] = Node('builtin_num_bin_op', [1], [], p[1:])


def p_builtin_num_un_op(p):
    """builtin_num_un_op : '+'
                         | '-'"""
    p[0] = Node('builtin_num_un_op', [1], [], p[1:])


def p_bool_literal(p):
    """bool_literal : FALSE
                    | TRUE"""
    p[0] = Node('bool_literal', [1], [], p[1:])


def p_int_literal(p):
    """int_literal : INTLIT"""
    p[0] = Node('int_literal', [1], [], p[1:])


def p_float_literal(p):
    """float_literal : FLOATLIT"""
    p[0] = Node('float_literal', [1], [], p[1:])


def p_string_literal(p):
    """string_literal : STRLIT"""
    p[0] = Node('string_literal', [1], [], p[1:])


def p_set_literal(p):
    """set_literal : '{' expr_star '}'"""
    p[0] = Node('set_literal', [1, 3], [2], p[1:])


def p_set_comp(p):
    """set_comp : '{' expr '|' comp_tail '}'"""
    p[0] = Node('set_comp', [1, 3, 5], [2, 4], p[1:])


def p_comp_tail(p):
    """comp_tail      : generator generator_star
                      | generator generator_star WHERE expr
       generator_star : epsilon
                      | ',' generator generator_star"""
    if len(p) == 2:
        p[0] = Node('generator_star', [], [1], p[1:])
    elif len(p) == 3:
        p[0] = Node('comp_tail', [], [1, 2], p[1:])
    elif len(p) == 4:
        p[0] = Node('generator_star', [1], [2, 3], p[1:])
    else:
        p[0] = Node('comp_tail', [3], [1, 2, 4], p[1:])


def p_generator(p):
    """generator  : IDENT ident_star IN expr
       ident_star : epsilon
                  | ',' IDENT ident_star"""
    if len(p) == 2:
        p[0] = Node('ident_star', [], [1], p[1:])
    elif len(p) == 4:
        p[0] = Node('ident_star', [1, 2], [3], p[1:])
    else:
        p[0] = Node('generator', [1, 3], [2, 4], p[1:])


def p_simple_array_literal(p):
    """simple_array_literal : '[' expr_star ']'"""
    p[0] = Node('simple_array_literal', [1, 3], [2], p[1:])


def p_simple_array_literal_2d(p):
    """simple_array_literal_2d : '[' '|' array_gen '|' ']'
       array_gen               : epsilon
                               | expr expr_star array_2d_gen"""
    if len(p) == 2:
        p[0] = Node('array_gen', [], [1], p[1:])
    elif len(p) == 4:
        p[0] = Node('array_gen', [], [1, 2, 3], p[1:])
    else:
        p[0] = Node('simple_array_literal_2d', [1, 2, 4, 5], [3], p[1:])


def p_array_2d_gen(p):
    """array_2d_gen : epsilon
                    | '|' array_gen array_2d_gen"""
    if len(p) == 2:
        p[0] = Node('array_2d_gen', [], [1], p[1:])
    else:
        p[0] = Node('array_2d_gen', [1], [2, 3], p[1:])


def p_simple_array_comp(p):
    """simple_array_comp : '[' expr '|' comp_tail ']'"""
    p[0] = Node('simple_array_comp', [1, 3, 5], [2, 4], p[1:])


def p_indexed_array_literal(p):
    """indexed_array_literal : '[' ']'
                             | '[' index_expr index_expr_star ']'
       index_expr_star       : epsilon
                             | ',' index_expr index_expr_star"""
    if len(p) == 2:
        p[0] = Node('index_expr_star', [], [1], p[1:])
    elif len(p) == 3:
        p[0] = Node('indexed_array_literal', [1, 2], [], p[1:])
    elif len(p) == 4:
        p[0] = Node('index_expr_star', [1], [2, 3], p[1:])
    else:
        p[0] = Node('indexed_array_literal', [1, 4], [2, 3], p[1:])


def p_index_expr(p):
    """index_expr : expr ':' expr"""
    p[0] = Node('index_expr', [2], [1, 3], p[1:])


def p_indexed_array_comp(p):
    """indexed_array_comp : '[' index_expr '|' comp_tail ']'"""
    p[0] = Node('indexed_array_comp', [1, 3, 5], [2, 4], p[1:])


def p_array_access_tail(p):
    """array_access_tail : '[' expr expr_star ']'"""
    p[0] = Node('array_access_tail', [1, 4], [2, 3], p[1:])


def p_tuple_literal(p):
    """tuple_literal : '(' expr expr_star ')'"""
    p[0] = Node('tuple_literal', [1, 4], [2, 3], p[1:])


def p_tuple_access_tail(p):
    """tuple_access_tail : '.' int_literal"""
    p[0] = Node('tuple_access_tail', [1], [2], p[1:])


def p_record_literal(p):
    """record_literal  : '(' named_expr named_expr_star ')'"""
    p[0] = Node('record_literal', [1, 4], [2, 3], p[1:])


def p_named_expr(p):
    """named_expr : IDENT ':' expr"""
    p[0] = Node('named_expr', [1, 2], [3], p[1:])


def p_record_access_tail(p):
    """record_access_tail : '.' IDENT"""
    p[0] = Node('record_access_tail', [1, 2], [], p[1:])



def p_enum_literal(p):
    """enum_literal    : IDENT '(' named_expr named_expr_star ')'
                       | IDENT '(' expr expr_star ')'
                       | IDENT"""
    if len(p) == 6:
        p[0] = Node('enum_literal', [1, 2, 5], [3, 4], p[1:])
    else:
        p[0] = Node('enum_literal', [1], [], p[1:])


def p_ann_literal(p):
    """ann_literal : IDENT
                   | IDENT '(' expr expr_star ')'"""
    if len(p) == 6:
        p[0] = Node('ann_literal', [1, 2, 5], [3, 4], p[1:])
    else:
        p[0] = Node('ann_literal', [1], [], p[1:])


def p_if_then_else_expr(p):
    """if_then_else_expr : IF expr THEN expr elseif_star ELSE expr ENDIF
       elseif_star       : epsilon
                         | ELSEIF expr THEN expr elseif_star"""
    if len(p) == 2:
        p[0] = Node('elseif_star', [], [1], p[1:])
    elif len(p) == 6:
        p[0] = Node('elseif_star', [1, 3], [2, 4, 5], p[1:])
    else:
        p[0] = Node('if_then_else_expr', [1, 3, 6, 8], [2, 4, 5, 7], p[1:])


def p_case_expr(p):
    """case_expr           : CASE expr '{' case_expr_case case_expr_case_star '}'
       case_expr_case_star : epsilon
                           | ',' case_expr_case case_expr_case_star"""
    if len(p) == 2:
        p[0] = Node('case_expr_case_star', [], [1], p[1:])
    elif len(p) == 4:
        p[0] = Node('case_expr_case_star', [1], [2, 3], p[1:])
    else:
        p[0] = Node('case_expr', [3, 6], [1, 2, 4, 5], p[1:])


def p_case_expr_case(p):
    """case_expr_case : IDENT RARROW expr"""
    p[0] = Node('case_expr_case', [1, 2], [3], p[1:])


def p_call_expr(p):
    """call_expr : ident_or_quoted_op
                 | ident_or_quoted_op '(' expr expr_star ')'"""
    if len(p) == 2:
        p[0] = Node('call_expr', [], [1], p[1:])
    else:
        p[0] = Node('call_expr', [2, 4], [1, 3], p[1:])


def p_let_expr(p):
    """let_expr           : LET '{' var_decl_item var_decl_item_star '}' IN expr
       var_decl_item_star : epsilon
                          | ',' var_decl_item var_decl_item_star"""
    if len(p) == 2:
        p[0] = Node('var_decl_item_star', [], [1], p[1:])
    elif len(p) == 4:
        p[0] = Node('var_decl_item_star', [1], [2, 3], p[1:])
    else:
        p[0] = Node('let_expr', [1, 2, 5, 6], [3, 4, 7], p[1:])


def p_gen_call_expr(p):
    """gen_call_expr : ident_or_quoted_op '(' comp_tail ')' '(' expr ')'"""
    p[0] = Node('gen_call_expr', [2, 4, 5, 7], [1, 3, 6], p[1:])


def p_annotations(p):
    """annotations : epsilon
                   | DOUBLECOL annotation annotations"""
    if len(p) == 2:
        p[0] = Node('annotations', [], [1], p[1:])
    else:
        p[0] = Node('annotations', [1], [2, 3], p[1:])


def p_annotation(p):
    """annotation : expr_atom_head expr_atom_tail"""
    p[0] = Node('annotation', [], [1, 2], p[1:])


## MISCELLANEOUS ELEMENTS ##

def p_ident_or_quoted_op(p):
    """ident_or_quoted_op : IDENT
                          | QUOT builtin_op QUOT"""
    if len(p) == 2:
        p[0] = Node('ident_or_quoted_op', [1], [], p[1:])
    else:
        p[0] = Node('ident_or_quoted_op', [1, 3], [2], p[1:])


def p_epsilon(p):
    """epsilon :"""
    p[0] = Node('epsilon', [], [], p[1:])


def p_ti_expr_and_id_star(p):
    """ti_expr_and_id_star : epsilon
                           | ',' ti_expr_and_id ti_expr_and_id_star"""
    if len(p) == 4:
        p[0] = Node('ti_expr_and_id_star', [1], [2, 3], p[1:])
    else:
        p[0] = Node('ti_expr_and_id_star', [], [1], p[1:])


def p_expr_star(p):
    """expr_star : epsilon
                 | ',' expr expr_star"""
    if len(p) == 4:
        p[0] = Node('expr_star', [1], [2, 3], p[1:])
    else:
        p[0] = Node('expr_star', [], [1], p[1:])


def p_named_expr_star(p):
    """named_expr_star : epsilon
                       | ',' named_expr named_expr_star"""
    if len(p) == 2:
        p[0] = Node('named_expr_star', [], [1], p[1:])
    else:
        p[0] = Node('named_expr_star', [1], [2, 3], p[1:])


def p_ti_expr_star(p):
    """ti_expr_star : epsilon
                    | ',' ti_expr ti_expr_star"""
    if len(p) == 4:
        p[0] = Node('ti_expr_star', [1], [2, 3], p[1:])
    else:
        p[0] = Node('ti_expr_star', [], [1], p[1:])


## Error rules for syntax errors ##
def p_error(p):
    print "Syntax error in input!"
    raise TypeError("unknown text at %r" % (p.value,))



# ## ITEMS ##

# def p_model_error(p):
#     """model : epsilon
#              | item ';' model"""
#     print 'p_model_error'


# def p_item_error(p):
#     """item : type_inst_syn_item
#             | enum_item
#             | include_item
#             | var_decl_item
#             | assign_item
#             | constraint_item
#             | solve_item
#             | output_item
#             | predicate_item
#             | test_item
#             | function_item
#             | annotation_item"""
#     print 'p_item_error'


# def p_type_inst_syn_item_error(p):
#     """type_inst_syn_item : TYPE IDENT annotations '=' ti_expr"""
#     print 'p_type_inst_syn_item_error'


# def p_enum_item_error(p):
#     """enum_item : ENUM IDENT annotations
#                  | ENUM IDENT annotations '=' enum_cases"""
#     print 'p_enum_item_error'


# def p_enum_cases_error(p):
#     """enum_cases     : '{' enum_case enum_case_star '}'
#        enum_case_star : epsilon
#                       | ',' enum_case enum_case_star"""
#     print 'p_enum_cases_error'


# def p_enum_case_error(p):
#     """enum_case : IDENT
#                  | IDENT '(' ti_expr_and_id ti_expr_and_id_star ')'"""
#     print 'p_enum_case_error'


# def p_ti_expr_and_id_error(p):
#     """ti_expr_and_id : ti_expr ':' IDENT"""
#     print 'p_ti_expr_and_id_error'


# def p_include_item_error(p):
#     """include_item : INCLUDE string_literal"""
#     print 'p_include_item_error'


# def p_var_decl_item_error(p):
#     """var_decl_item : ti_expr_and_id annotations
#                      | ti_expr_and_id annotations '=' expr"""
#     print 'p_var_decl_item_error'


# def p_assign_item_error(p):
#     """assign_item : IDENT '=' expr"""
#     print 'p_assign_item_error'


# def p_constraint_item_error(p):
#     """constraint_item : CONSTRAINT expr"""
#     print 'p_constraint_item_error'


# def p_solve_item_error(p):
#     """solve_item : SOLVE annotations SATISFY
#                   | SOLVE annotations MINIMIZE expr
#                   | SOLVE annotations MAXIMIZE expr"""
#     print 'p_solve_item_error'


# def p_output_item_error(p):
#     """output_item : OUTPUT expr"""
#     print 'p_output_item_error'


# def p_annotation_item_error(p):
#     """annotation_item : ANNOTATION IDENT params"""
#     print 'p_annotation_item_error'


# def p_predicate_item_error(p):
#     """predicate_item : PREDICATE operation_item_tail"""
#     print 'p_predicate_item_error'


# def p_test_item_error(p):
#     """test_item : TEST operation_item_tail"""
#     print 'p_test_item_error'


# def p_function_item_error(p):
#     """function_item : FUNCTION ti_expr ':' operation_item_tail"""
#     print 'p_function_item_error'


# def p_operation_item_tail_error(p):
#     """operation_item_tail : IDENT params annotations
#                            | IDENT params annotations '=' expr"""
#     print 'p_operation_item_tail_error'


# def p_params_error(p):
#     """params : epsilon
#               | '(' ti_expr_and_id ti_expr_and_id_star ')'"""
#     print 'p_params_error'


# ## TYPE-INST-EXPRESSIONS ##


# def p_ti_expr_error(p):
#     """ti_expr : '(' ti_expr ':' IDENT WHERE expr ')'
#                | base_ti_expr"""
#     print 'p_ti_expr_error'


# def p_base_ti_expr_error(p):
#     """base_ti_expr : var_par base_ti_expr_tail"""
#     print 'p_base_ti_expr_error'


# def p_var_par_error(p):
#     """var_par : epsilon
#                | PAR
#                | VAR"""
#     print 'p_var_par_error'


# def p_base_ti_expr_tail_error(p):
#     """base_ti_expr_tail : IDENT
#                          | BOOL
#                          | INT
#                          | FLOAT
#                          | STRING
#                          | set_ti_expr_tail
#                          | array_ti_expr_tail
#                          | tuple_ti_expr_tail
#                          | record_ti_expr_tail
#                          | ti_variable_expr_tail
#                          | ANN
#                          | op_ti_expr_tail
#                          | '{' expr expr_star '}'
#                          | num_expr DOTS num_expr"""
#     print 'p_base_ti_expr_tail_error'


# def p_set_ti_expr_tail_error(p):
#     """set_ti_expr_tail : SET OF ti_expr"""
#     print 'p_set_ti_expr_tail_error'


# def p_array_ti_expr_tail_error(p):
#     """array_ti_expr_tail : ARRAY '[' ti_expr ti_expr_star ']' OF ti_expr
#                           | LIST OF ti_expr"""
#     print 'p_tuple_ti_expr_tail_error'


# def p_tuple_ti_expr_tail_error(p):
#     """tuple_ti_expr_tail : TUPLE '(' ti_expr ti_expr_star ')'"""
#     print 'p_tuple_ti_expr_tail_error'


# def p_record_ti_exprtail_error(p):
#     """record_ti_expr_tail  : RECORD '(' ti_expr_and_id ti_expr_and_id_star ')'"""
#     print 'p_record_ti_exprtail_error'


# def p_ti_variable_expr_tail_error(p):
#     """ti_variable_expr_tail : IDENT
#                              | ANY IDENT"""
#     print 'p_ti_variable_expr_tail_error'


# def p_op_ti_expr_tail_error(p):
#     """op_ti_expr_tail : OP '(' ti_expr ':' '(' ti_expr ti_expr_star ')' ')'"""
#     print 'p_op_ti_expr_tail_error'


# ## EXPRESSIONS ##


# def p_expr_error(p):
#     """expr : expr_atom expr_binop_tail"""
#     print 'p_expr_error'


# def p_expr_atom_error(p):
#     """expr_atom : expr_atom_head expr_atom_tail annotations"""
#     print 'p_expr_atom_error'


# def p_expr_binop_tail_error(p):
#     """expr_binop_tail : epsilon
#                        | bin_op expr"""
#     print 'p_expr_binop_tail_error'


# def p_expr_atom_head_error(p):
#     """expr_atom_head : builtin_un_op expr_atom
#                       | '(' expr ')'
#                       | ident_or_quoted_op
#                       | '_'
#                       | bool_literal
#                       | int_literal
#                       | float_literal
#                       | string_literal
#                       | set_literal
#                       | set_comp
#                       | simple_array_literal
#                       | simple_array_literal_2d
#                       | indexed_array_literal
#                       | simple_array_comp
#                       | indexed_array_comp
#                       | tuple_literal
#                       | record_literal
#                       | enum_literal
#                       | ann_literal
#                       | if_then_else_expr
#                       | case_expr
#                       | let_expr
#                       | call_expr
#                       | gen_call_expr"""
#     print 'p_expr_atom_head_error'


# def p_expr_atom_tail_error(p):
#     """expr_atom_tail : epsilon
#                       | array_access_tail expr_atom_tail
#                       | tuple_access_tail expr_atom_tail
#                       | record_access_tail expr_atom_tail"""
#     print 'p_expr_atom_tail_error'


# def p_num_expr_error(p):
#     """num_expr : num_expr_atom num_expr_binop_tail"""
#     print 'p_num_expr_error'


# def p_num_expr_atom_error(p):
#     """num_expr_atom : num_expr_atom_head expr_atom_tail annotations"""
#     print 'p_num_expr_atom_error'


# def p_num_expr_binop_tail_error(p):
#     """num_expr_binop_tail : epsilon
#                            | num_bin_op num_expr"""
#     print 'p_num_expr_binop_tail_error'


# def p_num_expr_atom_head_error(p):
#     """num_expr_atom_head : builtin_num_un_op num_expr_atom
#                           | '(' num_expr ')'
#                           | ident_or_quoted_op
#                           | int_literal
#                           | float_literal
#                           | if_then_else_expr
#                           | case_expr
#                           | let_expr
#                           | call_expr
#                           | gen_call_expr"""
#     print 'p_num_expr_atom_head_error'


# def p_builtin_op_error(p):
#     """builtin_op : builtin_bin_op
#                   | builtin_un_op"""
#     print 'p_builtin_op_error'


# def p_bin_op_error(p):
#     """bin_op : builtin_bin_op
#               | QUOT IDENT QUOT"""
#     print 'p_bin_op_error'


# def p_builtin_bin_op_error(p):
#     """builtin_bin_op : IFF
#                       | SUF
#                       | NEC
#                       | DIS
#                       | XOR
#                       | CON
#                       | '<'
#                       | '>'
#                       | LEQ
#                       | GEQ
#                       | EQ
#                       | '='
#                       | DIF
#                       | IN
#                       | SUBSET
#                       | SUPERSET
#                       | UNION
#                       | DIFF
#                       | SYMDIFF
#                       | DOTS
#                       | INTERSECT
#                       | PP
#                       | builtin_num_bin_op"""
#     print 'p_builtin_bin_op_error'


# def p_builtin_un_op_error(p):
#     """builtin_un_op : NOT
#                      | builtin_num_un_op"""
#     print 'p_builtin_un_op_error'


# def p_num_bin_op_error(p):
#     """num_bin_op : builtin_num_bin_op
#                   | QUOT IDENT QUOT"""
#     print 'p_num_bin_op_error'


# def p_builtin_num_bin_op_error(p):
#     """builtin_num_bin_op : '+'
#                           | '-'
#                           | '*'
#                           | '/'
#                           | DIV
#                           | MOD"""
#     print 'p_builtin_num_bin_op_error'


# def p_builtin_num_un_op_error(p):
#     """builtin_num_un_op : '+'
#                          | '-'"""
#     print 'p_builtin_num_un_op_error'


# def p_bool_literal_error(p):
#     """bool_literal : FALSE
#                     | TRUE"""
#     print 'p_bool_literal_error'


# def p_int_literal_error(p):
#     """int_literal : INTLIT"""
#     print 'p_int_literal_error'


# def p_float_literal_error(p):
#     """float_literal : FLOATLIT"""
#     print 'p_float_literal_error'


# def p_string_literal_error(p):
#     """string_literal : STRLIT"""
#     print 'p_string_literal_error'


# def p_set_literal_error(p):
#     """set_literal : '{' expr_star '}'"""
#     print 'p_set_literal_error'


# def p_set_comp_error(p):
#     """set_comp : '{' expr '|' comp_tail '}'"""
#     print 'p_set_comp_error'


# def p_comp_tail_error(p):
#     """comp_tail      : generator generator_star
#                       | generator generator_star WHERE expr
#        generator_star : epsilon
#                       | ',' generator generator_star"""
#     print 'p_comp_tail_error'


# def p_generator_error(p):
#     """generator  : IDENT ident_star IN expr
#        ident_star : epsilon
#                   | ',' IDENT ident_star"""
#     print 'p_generator_error'


# def p_simple_array_literal_error(p):
#     """simple_array_literal : '[' expr_star ']'"""
#     print 'p_simple_array_literal_error'


# def p_simple_array_literal_2d_error(p):
#     """simple_array_literal_2d : '[' '|' array_gen '|' ']'
#        array_gen               : epsilon
#                                | expr expr_star array_2d_gen"""
#     print 'p_simple_array_literal_2d_error'


# def p_array_2d_gen_error(p):
#     """array_2d_gen : epsilon
#                     | '|' array_gen array_2d_gen"""
#     print 'p_array_2d_gen_error'


# def p_simple_array_comp_error(p):
#     """simple_array_comp : '[' expr '|' comp_tail ']'"""
#     print 'p_simple_array_comp_error'


# def p_indexed_array_literal_error(p):
#     """indexed_array_literal : '[' ']'
#                              | '[' index_expr index_expr_star ']'
#        index_expr_star       : epsilon
#                              | ',' index_expr index_expr_star"""
#     print 'p_indexed_array_literal_error'


# def p_index_expr_error(p):
#     """index_expr : expr ':' expr"""
#     print 'p_index_expr_error'


# def p_indexed_array_comp_error(p):
#     """indexed_array_comp : '[' index_expr '|' comp_tail ']'"""
#     print 'p_indexed_array_comp_error'


# def p_array_access_tail_error(p):
#     """array_access_tail : '[' expr expr_star ']'"""
#     print 'p_array_access_tail_error'


# def p_tuple_literal_error(p):
#     """tuple_literal : '(' expr expr_star ')'"""
#     print 'p_tuple_literal_error'


# def p_tuple_access_tail_error(p):
#     """tuple_access_tail : '.' int_literal"""
#     print 'p_tuple_access_tail_error'


# def p_record_literal_error(p):
#     """record_literal  : '(' named_expr named_expr_star ')'"""
#     print 'p_record_literal_error'


# def p_named_expr_error(p):
#     """named_expr : IDENT ':' expr"""
#     print 'p_named_expr_error'


# def p_record_access_tail_error(p):
#     """record_access_tail : '.' IDENT"""
#     print 'p_record_access_tail_error'


# def p_enum_literal_error(p):
#     """enum_literal    : IDENT '(' named_expr named_expr_star ')'
#                        | IDENT '(' expr expr_star ')'
#                        | IDENT"""
#     print 'p_enum_literal_error'


# def p_ann_literal_error(p):
#     """ann_literal : IDENT
#                    | IDENT '(' expr expr_star ')'"""
#     print 'p_ann_literal_error'


# def p_if_then_else_expr_error(p):
#     """if_then_else_expr : IF expr THEN expr elseif_star ELSE expr ENDIF
#        elseif_star       : epsilon
#                          | ELSEIF expr THEN expr elseif_star"""
#     print 'p_if_then_else_expr_error'


# def p_case_expr_error(p):
#     """case_expr           : CASE expr '{' case_expr_case case_expr_case_star '}'
#        case_expr_case_star : epsilon
#                            | ',' case_expr_case case_expr_case_star"""
#     print 'p_case_expr_error'


# def p_case_expr_case_error(p):
#     """case_expr_case : IDENT RARROW expr"""
#     print 'p_case_expr_case_error'


# def p_call_expr_error(p):
#     """call_expr : ident_or_quoted_op
#                  | ident_or_quoted_op '(' expr expr_star ')'"""
#     print 'p_call_expr_error'


# def p_let_expr_error(p):
#     """let_expr           : LET '{' var_decl_item var_decl_item_star '}' IN expr
#        var_decl_item_star : epsilon
#                           | ',' var_decl_item var_decl_item_star"""
#     print 'p_let_expr_error'


# def p_gen_call_expr_error(p):
#     """gen_call_expr : ident_or_quoted_op '(' comp_tail ')' '(' expr ')'"""
#     print 'p_gen_call_expr_error'


# def p_annotations_error(p):
#     """annotations : epsilon
#                    | DOUBLECOL annotation annotations"""
#     print 'p_annotations_error'


# def p_annotation_error(p):
#     """annotation : expr_atom_head expr_atom_tail"""
#     print 'p_annotation_error'


# ## MISCELLANEOUS ELEMENTS ##


# def p_ident_or_quoted_op_error(p):
#     """ident_or_quoted_op : IDENT
#                           | QUOT builtin_op QUOT"""
#     print 'p_ident_or_quoted_op_error'


# def p_epsilon_error(p):
#     """epsilon :"""
#     print 'p_epsilon_error'


# def p_ti_expr_and_id_star_error(p):
#     """ti_expr_and_id_star : epsilon
#                            | ',' ti_expr_and_id ti_expr_and_id_star"""
#     print 'p_ti_expr_and_id_star_error'


# def p_expr_star_error(p):
#     """expr_star : epsilon
#                  | ',' expr expr_star"""
#     print 'p_expr_star_error'


# def p_named_expr_star_error(p):
#     """named_expr_star : epsilon
#                        | ',' named_expr named_expr_star"""
#     print 'p_named_expr_star_error'


# def p_ti_expr_star_error(p):
#     """ti_expr_star : epsilon
#                     | ',' ti_expr ti_expr_star"""
#     print 'p_ti_expr_star_error'



# ## Build the parser
# parser = yacc.yacc()

# filename1, filename2 = sys.argv[1], sys.argv[2]


# def load_file(filename):
#     f = open(filename, 'r')
#     s = ''
#     for line in f:
#         s += line
#     f.close()
#     return parser.parse(s)


# root1 = load_file(filename1)
# root2 = load_file(filename2)

# # print root
# tree_vector1 = root1.create_tree_vector()
# tree_vector2 = root2.create_tree_vector()

# lcs_vector = lcs_tree_vector(tree_vector1, tree_vector2,
#                              len(tree_vector1), len(tree_vector2))

# for n in lcs_vector:
#     print n

# for n in reversed(lcs_vector):
#     print n[0].dump_subtree_terminals(n[1])[0]


# # print tree1
# # print '=========================================='
# # print tree2
# # print '------------------------------------------'

# # print lcs_print(tree1, tree2, len(tree1), len(tree2))



# # while True:
# #     try:
# #         s = raw_input('calc > ')
# #     except EOFError:
# #         break
# #     if not s:
# #         continue
# #     result = parser.parse(s)
# #     print result

def compute_snippet_elements(s1, s2):
    """Returns the snippets generated from 's1' and 's2'.
    """
    snippet_elems = []
    parser = yacc.yacc()
    root1 = parser.parse(s1)
    root2 = parser.parse(s2)
    tree_vector1 = root1.create_tree_vector()
    tree_vector2 = root2.create_tree_vector()
    lcs_tree_vector = lcs_vector(tree_vector1, tree_vector2,
                                 len(tree_vector1), len(tree_vector2))
    for n in reversed(lcs_tree_vector):
        snippet_elems.append(n[0].dump_subtree_terminals(n[1])[0])
    return snippet_elems
