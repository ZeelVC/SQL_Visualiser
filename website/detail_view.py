import sqlparse
import re
from graphviz import Digraph
from flask import flash, render_template

#from .logic1 import check_syntax
 
#To create a different for data structure module.
class Node:
    def __init__(self, value):
        self.key_ele = value
        self.child = []
   
    def visualize(self, graph, parent_node=None):
        node_name = str(id(self))
        node_label = str(self.key_ele)
        graph.node(node_name, label=node_label)
 
        if parent_node:
            graph.edge(parent_node, node_name)
        for child in self.child:
            child.visualize(graph, node_name)
 
#To create a different module for aggregate function.
def aggregate(func_str):
    aggregates = ['MIN', 'MAX', 'SUM', 'AVG', 'COUNT']
    return any(func_str.startswith(agg + '(') for agg in aggregates)

is_cte_in_main = False
#To create a different module for each funtion of sql_to_graph function.
def sql_to_graph(parsed, root, ind, list_of_cte):
    global is_cte_in_main

    #maintaining current_node
    current_node = root
    parent_node = root
    tableNode = Node('0')
    tableNode_list = []
    isaggr = False
    while ind < len(parsed):
        clause = parsed[ind]
        #close bracket code, indication there was a subquery
        if clause in {')', ')WITHEND', '),WITHEND', 'UNION', 'WITHUNION'}:
            break

        #select condition
        #Also need to optimise the aggregate function code is there is a space in aggregate function.
        elif clause.upper() == 'SELECT':
            temp = Node('SELECT')
            j = ind + 1
            str = 'SELECT\n\n( '
            aggr = 'AGGREGATE \n\n'
            dict = {}
            key_value = 1
            key_str = ''
            while parsed[j].upper() != 'FROM':
                if aggregate(parsed[j].upper()):
                    aggr+=parsed[j].upper()
                    key_str += parsed[j]
                    while j < len(parsed) and parsed[j + 1].upper() != 'FROM' and parsed[j + 1][len(parsed[j + 1]) - 1] != ',':
                        aggr += ' ' + parsed[j + 1].upper()
                        key_str += ' ' + parsed[j + 1]
                        j+=1
                    if parsed[j + 1][len(parsed[j + 1]) - 1] == ',':
                        aggr += ' ' + parsed[j + 1] 
                        key_str += ' ' + parsed[j + 1]
                        j += 1
                    dict[key_value] = []
                    dict[key_value].append(key_str)
                    key_value+=1
                    str += key_str + '\n'
                    key_str = ''
                    aggr +='\n\n'
                    isaggr = True
                elif parsed[j][len(parsed[j]) - 1] == ',':
                    str += parsed[j] + '\n'
                    key_str += parsed[j]
                    dict[key_value] = []
                    dict[key_value].append(key_str)
                    key_value+=1
                    key_str = ''
                else:
                    str += parsed[j] + ' '
                    key_str+=parsed[j] + ' '
                j +=1
            ind = j - 1
            dict[key_value] = []
            dict[key_value].append(key_str)
            key_value+=1
            key_str = ''
            str += ' )'
            temp.key_ele = str  
            parent_node = temp
            current_node = parent_node
            print(dict)

        #From condition
        elif clause.upper() == 'FROM':
            if parsed[ind + 1] == '(':
                ind+=1
                continue
            else:
                tableNode = Node(parsed[ind + 1])
                j = ind + 1
                str = 'FROM\n\n( ' 
                cte_table_name = ''
                while j < len(parsed) and parsed[j].upper() not in {')', 'WHERE', 'JOIN', 'GROUP', 'ORDER', 'LIMIT', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'LEFT', 'INNER', 'SELECT'}:
                    if parsed[j][len(parsed[j]) - 1] == ',':
                        str += parsed[j]
                        cte_table_name += parsed[j][0 : len(parsed[j]) - 1]
                        tableNode.key_ele = 'SELF JOIN'
                        table = Node(cte_table_name)
                        tableNode.child.append(table)
                        for table_name in list_of_cte:
                            if cte_table_name[0:len(table_name.key_ele) - 6] == table_name.key_ele[6:]:
                                is_cte_in_main = True
                                table.child.append(table_name)
                                break
                        cte_table_name = ''
                        str += '\n'
                    else:
                        cte_table_name+=parsed[j]
                        str += ' ' + parsed[j]
                    j+=1
                if tableNode.key_ele == 'SELF JOIN':
                    table = Node(cte_table_name)
                    tableNode.child.append(table)
                    for table_name in list_of_cte:
                        if cte_table_name[0:len(table_name.key_ele) - 6] == table_name.key_ele[6:]:
                            is_cte_in_main = True
                            table.child.append(table_name)
                            break
                if tableNode.key_ele != 'SELF JOIN':  
                    str+= ' )'      
                    tableNode.key_ele = str
                    for table_name in list_of_cte:
                        if cte_table_name[0:len(table_name.key_ele) - 6] == table_name.key_ele[6:]:
                            is_cte_in_main = True
                            tableNode.child.append(table_name)
                            break
                tableNode_list.append(tableNode)
 
        #Where condition
        elif clause.upper() == 'WHERE':
            j = ind + 1
            str = 'WHERE\n\n( '
            while j < len(parsed) and parsed[j].upper() not in {')', 'JOIN', 'GROUP', 'ORDER', 'LIMIT', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
                if parsed[j] == ')':
                    break
                if parsed[j] == '(':
                    str+='Subquery' 
                    j+=1
                    count = 1
                    while count != 0:
                        if j < len(parsed) and count != 0 and parsed[j] == ')':
                            count-=1
                        if j < len(parsed) and parsed[j] == '(':
                            count+=1
                        j+=1
                    j-=1
                elif parsed[j].upper() == 'AND' or parsed[j].upper() == 'OR':
                    str += '\n'+parsed[j].upper()+' '
                #    temp = Node(str)
                #    current_node.child.append(temp)
                #    str = 'WHERE' + '\n\n( '
                else:
                    #if parsed[j][len(parsed[j]) - 1] == ',':
                    #    str += parsed[j] + '\n'
                    #else:
                    str += parsed[j] + ' '
                j+=1
            str += ' )'
            temp = Node(str)
            current_node.child.append(temp)


        #Join condition
        elif clause.upper() == 'JOIN':
            join_type = clause.upper() if clause.upper() in {'LEFT', 'RIGHT', 'INNER', 'FULL', 'CROSS', 'SELF', 'OUTER'} else ''
            str = f'{join_type} JOIN\n\n( '
            j = ind + 1
            second_table = 'FROM\n\n( '
            cte_table_name = ''
            list_of_cte_table = []
            while parsed[j].upper() != 'ON':
                if parsed[j][len(parsed[j]) - 1] == ',':
                    second_table += parsed[j]
                    cte_table_name += parsed[j][0 : len(parsed) - 1]
                    for table_name in list_of_cte:
                        if table_name.key_ele[6:] == cte_table_name[0:len(table_name.key_ele) - 6]:
                            is_cte_in_main = True
                            list_of_cte_table.append(table_name)
                            break
                    cte_table_name = ''
                elif parsed[j] == '(':
                    second_table += 'Subquery'
                    j+=1
                    count = 1
                    while count != 0:
                        if j < len(parsed) and count != 0 and parsed[j] == ')':
                            count-=1
                        if j < len(parsed) and parsed[j] == '(':
                            count+=1
                        j+=1
                    j-=1
                else:
                    second_table += ' ' + parsed[j]
                    cte_table_name += parsed[j]
                j+=1
            for table_name in list_of_cte:
                if table_name.key_ele[6:] == cte_table_name[0:len(table_name.key_ele) - 6]:
                    is_cte_in_main = True
                    list_of_cte_table.append(table_name)
                    break
            while j < len(parsed) and parsed[j].upper() not in {')', 'WHERE', 'GROUP', 'JOIN', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
                if parsed[j][len(parsed[j]) - 1] == ',' or parsed[j].upper() == 'AND' or parsed[j].upper() == 'OR':
                    str += parsed[j] + '\n'
                else:
                    str += parsed[j] + ' '
                j+=1
            str += ' )'
            temp = Node(str)
            temp.child.append(parent_node)
            parent_node = temp    
            #if parsed[ind + 1] != '(':
            #    temp = Node(second_table)
            #    parent_node.child.append(temp)
            #    for table_name in list_of_cte_table:
            #        temp.child.append(table_name)
            second_table += ' )'
            temp = Node(second_table)
            for table_name in list_of_cte_table:
                temp.child.append(table_name)
            tableNode_list.append(temp)
 
        #group by condition
        elif clause.upper() == 'GROUP':
            j = ind + 2
            str = 'GROUP BY\n\n( '
            while j < len(parsed) and parsed[j].upper() not in {')', 'HAVING', 'ORDER', 'LIMIT', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
                pattern = r'^-?\d+$'
                if parsed[j][len(parsed[j]) - 1] == ',':
                    string_result = bool(re.match(pattern, parsed[j][:-1]))
                    if string_result: 
                        str += dict[int(parsed[j][0:len(parsed[j]) - 1])][0] + '\n'
                    else:
                        str += parsed[j] + '\n'
                else:
                    string_result = bool(re.match(pattern, parsed[j][-1]))
                    if string_result: 
                        str += dict[int(parsed[j])][0] + ' '
                    else:
                        str += parsed[j] + ' '
                j+=1
            str += ' )'
            temp = Node(str)
            temp.child.append(parent_node)
            parent_node = temp
 
        #Having condition
        elif clause.upper() == 'HAVING':
            j = ind + 1
            str = 'HAVING' + '\n\n( '
            while j < len(parsed) and parsed[j].upper() not in {')', 'ORDER', 'LIMIT', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
                if parsed[j][len(parsed[j]) - 1] == ',':
                    str += parsed[j] + '\n'
                else:
                    str += parsed[j] + ' '
                j+=1
            str += ' )'
            temp = Node(str)
            temp.child.append(parent_node)
            parent_node = temp
       
        #Order by condition
        elif clause.upper() == 'ORDER':
            j = ind + 2
            str = 'ORDER BY\n\n( '
            while j < len(parsed) and parsed[j].upper() not in {')', 'LIMIT', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
                pattern = r'^-?\d+$'
                if parsed[j][len(parsed[j]) - 1] == ',':
                    string_result = bool(re.match(pattern, parsed[j][:-1]))
                    if string_result: 
                        str += dict[int(parsed[j][0:len(parsed[j]) - 1])][0] + '\n'
                    else:
                        str += parsed[j] + '\n'
                else:
                    string_result = bool(re.match(pattern, parsed[j][-1]))
                    if string_result: 
                        str += dict[int(parsed[j])][0] + ' '
                    else:
                        str += parsed[j] + ' '
                j += 1
            str += ' )'
            temp = Node(str)
            temp.child.append(parent_node)
            parent_node = temp
 
        #LIMIT condition
        elif clause.upper() == 'LIMIT' and parsed[j].upper() not in {'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
            j = ind + 1
            str = 'LIMIT' + '\n\n( '
            while j < len(parsed) and parsed[j] != ')':
                if parsed[j][len(parsed[j]) - 1] == ',':
                    str += parsed[j] + '\n'
                else:
                    str += parsed[j] + ' '
                j+=1
            str += ' )'
            temp = Node(str)
            temp.child.append(parent_node)
            parent_node = temp
 
        #subquery
            #in case join, we had to add the subquery to the parent node
            #while in rest cases to current node
        elif clause == '(' and parsed[ind + 1].upper() == 'SELECT':
            root_subquery = Node('null')
            #j = ind + 2
            #str = 'SELECT' + '\n\n( '
            #aggr = 'AGGREGATE \n\n'
            #isaggr = False
            #while parsed[j].upper() != 'FROM':
            #    if aggregate(parsed[j].upper()):
            #        aggr+= ' ' + parsed[j].upper()
            #        isaggr = True
            #    elif parsed[j][len(parsed[j]) - 1] == ',':
            #        str += parsed[j] + '\n'
            #    else:
            #        str += parsed[j] + ' '
            #    j+=1
            #str += ' )'
            #root_subquery.key_ele = str
            root_subquery = sql_to_graph(parsed, root_subquery, ind + 1, list_of_cte)
            if isaggr:
                temp = Node(aggr)
                temp.child.append(root_subquery)
                root_subquery = temp
            tmp = Node('Subquery')
            if parsed[ind - 1].upper() == 'FROM':
                tableNode.child.append(tmp)
                tmp.child.append(root_subquery)
                tableNode = tmp
                tableNode_list.append(tableNode)
            elif parsed[ind - 1].upper() in {'WHERE', 'AND', 'OR', '=', '>', '<', 'IN', 'LIKE', 'AS', '!=', 'EXISTS'}:
                for node in current_node.child:
                    if node.key_ele.find('Subquery') != -1:
                        tmp.child.append(root_subquery)
                        node.child.append(tmp)
                        break
            elif parsed[ind - 1].upper() == 'JOIN':
                tmp.child.append(root_subquery)
                for table_Node in tableNode_list:
                    if table_Node.key_ele.find('Subquery') != -1:
                        table_Node.child.append(tmp)
                        break
            else:
                current_node.child.append(root_subquery)
            count = 1
            ind += 1
            while count != 0:
                if ind < len(parsed) and count != 0 and parsed[ind] == ')':
                    count-=1
                if ind < len(parsed) and parsed[ind] == '(':
                    count+=1
                ind+=1
            ind -= 1
        ind += 1
    #at last of each adding tableNode as per approach.
    if len(current_node.child) >=1:
        for node in current_node.child:
            for table_Node in tableNode_list:
                node.child.append(table_Node)
    else:
        for table_Node in tableNode_list:
                current_node.child.append(table_Node)
    if isaggr:
        temp = Node(aggr)
        temp.child.append(parent_node)
        parent_node = temp
    return parent_node
 
# print the graph
def print_graph(root):
    if len(root.child) == 0:
        return
    queue = []
 
    queue.append(root)
 
    while len(queue) > 0:
        node = queue.pop(0)
        print(node.key_ele + ':  [', end="")
        i = 1
        for ele in node.child:
            if i < len(node.child):
                print(ele.key_ele + '; ')
            else:
                print(ele.key_ele + ']')
            i += 1
            queue.append(ele)
        if len(node.child) == 0:
            print(']')
 
       
# main function
def main2(query):
    global is_cte_in_main
    
    # Preprocessing the query
    query = query.replace('\n', ' ').replace(', ', ',').replace(',', ', ')
    original_query = query

    # Remove the following line as check_syntax function and related implementation is not provided.
    # if check_syntax(query, 0):
    #     flash("SQL Syntax Error:", "error")
    #     return render_template("SQLViz.html")

    try:
        parsed = query.split()
        list_of_cte = []
        graph = Digraph()
        
        # Parsing Common Table Expressions (CTEs)
        i = 0
        while i < len(parsed):
            if parsed[i].upper() == 'WITH':
                cte_str = 'CTE -'
                i += 1
                while i < len(parsed) and parsed[i].upper() != 'AS':
                    cte_str += ' ' + parsed[i]
                    i += 1
                cte_node = Node(cte_str)
                list_of_cte.append(cte_node)
                while i < len(parsed) and parsed[i] not in {')', '),'}:
                    if parsed[i].upper() == 'SELECT':
                        parsed[i] = 'WITHSELECT'
                    if parsed[i].upper() == 'UNION':
                        parsed[i] = 'WITHUNION'
                    i += 1
                if parsed[i] in {')', '),'}:
                    if parsed[i] == '),':
                        parsed.insert(i + 1, 'WITH')
                    parsed[i] += 'WITHEND'
            i += 1

        list_of_main_root = []
        root = Node('Null')
        ind_of_cte = 0
        cte_root = Node('CTE')
        is_main_root = False
        is_create_node = False
        is_cte = False

        # Main parsing logic
        i = 0
        while i < len(parsed):
            if parsed[i].upper() == 'CREATE':
                is_create_node = True
                create_node = Node(parsed[i].upper())
                i += 1
                while parsed[i].upper() != 'TABLE':
                    create_node.key_ele += ' ' + parsed[i].upper()
                    i += 1
                create_node.key_ele += ' ' + parsed[i].upper() + '\n'
                i += 1
                while parsed[i].upper() != 'AS':
                    if parsed[i][-1] == ',':
                        create_node.key_ele += parsed[i] + '\n'
                    else:
                        create_node.key_ele += parsed[i] + ' '
                    i += 1

            if parsed[i].upper() == 'SELECT':
                if i == 0 or (i != 0 and parsed[i - 1] != '('):
                    root = Node('Null')
                    root = sql_to_graph(parsed, root, i, list_of_cte)
                    print_graph(root)
                    is_main_root = True
                    list_of_main_root.append(root)

            elif parsed[i].upper() == 'UNION':
                union_node = Node('UNION ALL' if parsed[i + 1].upper() != 'ALL' else 'UNION')
                union_node.child.append(root)
                root = union_node
                root1 = Node('Null')
                root1 = sql_to_graph(parsed, root1, i + 1 if parsed[i + 1].upper() != 'ALL' else i + 2, list_of_cte)
                i += 1 if parsed[i + 1].upper() != 'ALL' else 2
                root.child.append(root1)

            elif parsed[i] == 'WITHSELECT':
                root = Node('Null')
                parsed[i] = 'SELECT'
                root = sql_to_graph(parsed, root, i, list_of_cte)
                is_cte = True

            elif parsed[i] == 'WITHUNION':
                parsed[i] = 'UNION'
                union_node = Node('UNION ALL' if parsed[i + 1].upper() != 'ALL' else 'UNION')
                union_node.child.append(root)
                root = union_node
                root1 = Node('Null')
                parsed[i + 1 if parsed[i + 1].upper() != 'ALL' else i + 2] = 'SELECT'
                root1 = sql_to_graph(parsed, root1, i + 1 if parsed[i + 1].upper() != 'ALL' else i + 2, list_of_cte)
                i += 1 if parsed[i + 1].upper() != 'ALL' else 2
                root.child.append(root1)

            elif parsed[i] in {')WITHEND', '),WITHEND'}:
                list_of_cte[ind_of_cte].child.append(root)
                root = list_of_cte[ind_of_cte]
                cte_root.child.append(root)
                ind_of_cte += 1

            i += 1

        if not is_main_root:
            root = cte_root

        if is_create_node:
            create_node.child.append(root)
            root = create_node

        if not is_cte_in_main and is_cte and is_main_root:
            cte_root.visualize(graph)

        print_graph(root)
        root.visualize(graph)
        graph.render('node_structure2', format='png', cleanup=True)
        
        return 'node_structure2.png'

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
 
if __name__ == '__main__':
    query = "Select job_id,salary from job group by 1,2"
    main2(query)
