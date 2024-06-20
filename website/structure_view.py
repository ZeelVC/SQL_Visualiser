import sqlparse
from graphviz import Digraph
from flask import flash, render_template
 
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
 
def aggregate(func_str):
    aggregates = ['MIN', 'MAX', 'SUM', 'AVG', 'COUNT']
    return any(func_str.startswith(agg + '(') for agg in aggregates)



is_cte_in_main = False
def sql_to_graph(parsed, root, ind, list_of_cte):
    global is_cte_in_main
    #print(is_cte_in_main)
    #maintaining current_node
    current_node = root
    parent_node = root
    tableNode = Node('Null')
    while ind < len(parsed):
        clause = parsed[ind]
        #close bracket code, indication there was a subquery
        if clause in {')', ')WITHEND', '),WITHEND', 'UNION', 'WITHUNION'}:
            break
 
        #select condition
        elif clause.upper() == 'SELECT':
            tmp = Node('SELECT')
            j = ind + 1
            str = 'SELECT'
            aggr = 'AGGREGATE'
            isaggr = False
            while parsed[j].upper() != 'FROM':
                if aggregate(parsed[j].upper()):
                    isaggr = True
                    break
                j+=1
            #tmp.key_ele = str
            #parent_node = tmp
            #current_node = parent_node

 
        #From condition
        elif clause.upper() == 'FROM':
            if parsed[ind + 1] == '(':
                ind+=1
                continue
            else:
                '''tableNode = Node(parsed[ind + 1])
                j = ind + 2
                str = parsed[ind + 1]
                while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() != 'WHERE' and parsed[j].upper() != 'JOIN' and parsed[j].  upper() != 'GROUP' and parsed[j].upper() != 'ORDER' and parsed[j].upper() != 'LIMIT' and parsed[j].upper() != 'UNION':
                    str+=' ' + parsed[j]
                    j+=1
                tableNode.key_ele = str
                '''
                tableNode = Node(parsed[ind + 1])
                j = ind + 1
                str = '' 
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
                    tableNode.key_ele = str
                    for table_name in list_of_cte:
                        if cte_table_name[0:len(table_name.key_ele) - 6] == table_name.key_ele[6:]:
                            is_cte_in_main = True
                            tableNode.child.append(table_name)
                            break
                
 
        #Where condition
        elif clause.upper() == 'WHERE':
            if parsed[ind + 1] == '(':
                #temp = Node('WHERE')
                #current_node.child.append(temp)
                #current_node = temp
                ind+=1
                continue
            else:
                j = ind + 1
                str = 'WHERE'
                '''while j < len(parsed) and parsed[j] != '(' and parsed[j].upper() != 'JOIN' and parsed[j].upper() != 'GROUP':
                    str += ' ' + parsed[j]
                    j+=1
                '''
                #temp = Node(str)
                #current_node.child.append(temp)
                #current_node = temp
 
 
        #Join condition
        elif clause.upper() == 'JOIN':
            join_type = clause.upper() if clause.upper() in {'LEFT', 'RIGHT', 'INNER', 'FULL', 'CROSS', 'SELF', 'OUTER'} else ''
            str = f'{join_type} JOIN'
            j = ind + 1
            second_table = ''
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
                else:
                    second_table += ' ' + parsed[j]
                    cte_table_name += parsed[j]
                j+=1
            for table_name in list_of_cte:
                if table_name.key_ele[6:] == cte_table_name[0:len(table_name.key_ele) - 6]:
                    is_cte_in_main = True
                    list_of_cte_table.append(table_name)
                    break
            '''while parsed[j] != 'ON':
                j+=1
            while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() != 'GROUP' and parsed[j].upper() != 'JOIN':
                str += ' ' + parsed[j]
                j+=1
            '''
            if parent_node.key_ele == 'Null':
                temp = Node(str)
                parent_node = temp
                current_node = temp
            else:
                temp = Node(str)
                temp.child.append(parent_node)
                parent_node = temp    
            
            if parsed[ind + 1] != '(':
                temp = Node(second_table)
                parent_node.child.append(temp)
                for table_name in list_of_cte_table:
                    temp.child.append(table_name)
 
        #group by condition
        elif clause.upper() == 'GROUP':
            j = ind + 2
            str = 'GROUP BY'
            '''while j < len(parsed) and parsed[j].upper() != 'HAVING' and parsed[j].upper() != 'ORDER' and parsed[j].upper() != 'LIMIT':
                str+=' ' + parsed[j]
                j+=1
            '''
            #temp = Node(str)
            #temp.child.append(parent_node)
            #parent_node = temp
 
        #Having condition
        elif clause.upper() == 'HAVING':
            j = ind + 1
            str = 'HAVING'
            '''while j < len(parsed) and parsed[j].upper() != 'ORDER' and parsed[j].upper() != 'LIMIT':
                str+=' ' + parsed[j]
                j+=1
            '''
            #temp = Node(str)
            #temp.child.append(parent_node)
            #parent_node = temp
       
        #Order by condition
        elif clause.upper() == 'ORDER':
            j = ind + 2
            str = 'ORDER BY'
            '''while j < len(parsed) and parsed[j].upper() != 'LIMIT':
                str+=' ' + parsed[j]
                j+=1
            '''
            #temp = Node(str)
            #temp.child.append(parent_node)
            #parent_node = temp
 
        #LIMIT condition
        elif clause.upper() == 'LIMIT':
            j = ind + 1
            str = 'LIMIT'
            '''while j < len(parsed):
                str+=' ' + parsed[j]
                j+=1
            '''
            #temp = Node(str)
            #temp.child.append(parent_node)
            #parent_node = temp
 
        #subquery
            #in case join, we had to add the subquery to the parent node
            #while in rest cases to current node
        elif clause == '(' and parsed[ind + 1].upper() == 'SELECT':
            root_subquery = Node('Null')
            '''j = ind + 2
            str = 'SELECT'
            while parsed[j].upper() != 'FROM':
                str+=' ' + parsed[j]
                j+=1
            root_subquery.key_ele = str
            '''
            
            root_subquery = sql_to_graph(parsed, root_subquery, ind + 1, list_of_cte)
            
            tmp = Node('Subquery')
            if parsed[ind - 1].upper() in {'FROM', 'WHERE', 'AND', 'OR', '=', '>', '<', 'IN', 'LIKE', 'AS', '!=', 'EXISTS'}:
                tableNode.child.append(tmp)
                tmp.child.append(root_subquery) 
                if tableNode.key_ele == 'Null':
                    tableNode = tableNode.child[0]
            elif parsed[ind - 1].upper() == 'JOIN':
                parent_node.child.append(tmp)
                tmp.child.append(root_subquery)
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
            ind-=1
        ind += 1
    #at last of each adding tableNode as per approach.
    if current_node.key_ele == 'Null':
        parent_node = tableNode
    else:
        current_node.child.append(tableNode)
    #if isaggr:
    #    temp = Node(aggr)
    #    temp.child.append(parent_node)
    #    parent_node = temp
    #print(is_cte_in_main)
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
 
def check_syntax(query, ind):   
    if query[ind : ind + 6].upper() != 'SELECT':
        return True
    while ind < len(query):
        if query[ind : ind + 6].upper() == 'SELECT':
            if ind + 6 > len(query):
                print(1)
                return True
            if query[ind + 6] != ' ':
                print(2)
                return True
            keywords = ('FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT')

            if any(query[ind+6:ind+len(keyword)].upper() == keyword for keyword in keywords):
                print(3)
                return True
            j = ind+6
            while query[j:j+4] != 'FROM':
                if query[j] == ',':
                    if query[j + 1] != ' ':
                        print(29)
                        return True
                j+=1
        elif query[ind:ind+4].upper() == 'FROM':
            if ind + 4 > len(query) or ind+5 > len(query):
                print(4)
                return True
            if query[ind+4] != ' ':
                print(5)
                return True
            keywords = ('FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT')

            if any(query[ind+4:ind+4+len(keyword)].upper() == keyword for keyword in keywords):
                print(6)
                return True
        elif query[ind] == '(' and query[ind+1] == ' ':
            if (query[ind-2:ind] != ', ' and query[ind-3:ind].upper() not in ('AVG', 'MIN', 'MAX', 'SUM', 'COUNT')):
                if ind+1 > len(query):
                    print(30)
                    return True
                if query[ind+1] != ' ':
                    print(31)
                    return True
                if query[ind+2:ind+8].upper() != 'SELECT':
                    print(32)
                    return True 
                count = 1
                j = ind + 1
                while j < len(query) and count != 0:
                    if count != 0 and query[j] == ')' and query[j - 1] == ' ':
                        count -= 1
                    elif query[j] == '(' and query[j + 1] == ' ':
                        count += 1
                    j+=1
                if count != 0:
                    print(33)
                    return True
        elif query[ind:ind+5].upper() == 'WHERE':
            if ind + 5 > len(query):
                print(7)
                return True
            if query[ind+5] != ' ':
                print(8)
                return True
            valid_keywords = ['FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT']

            if any(query[ind+5:ind+len(keyword)+5].upper() == keyword for keyword in valid_keywords):

                print(9)
                return True
        elif query[ind : ind+4].upper() == 'JOIN':
            if ind + 4 > len(query):
                print(17)
                return True
            if query[ind+4] != ' ':
                print(18)
                return True
            keywords_to_check = ['FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT']

            if any(query[ind+4:ind+4+len(keyword)].strip().upper() == keyword for keyword in keywords_to_check):
                print(19)
                return True
        elif query[ind:ind+3].upper()=='AND':
            if ind + 3 > len(query):
                print(10)
                return True
            if query[ind+3] != ' ':
                print(11)
                return True
            keywords_to_check = ['FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT']

            if any(query[ind+3:ind+3+len(keyword)].strip().upper() == keyword for keyword in keywords_to_check):
                print(12)
                return True
        elif (query[ind:ind+5].upper() =='ORDER' or query[ind:ind+5].upper() == 'GROUP') and query[ind+6 : ind+8]=='BY':
            if ind + 5 > len(query):
                print(13)
                return True
            if query[ind+5] != ' ':
                print(14)
                return True
            if query[ind+6:ind+8] != 'BY':
                print(15)
                return True
            keywords_to_check = ['FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT']

            if any(query[ind+5:ind+5+len(keyword)].strip().upper() == keyword for keyword in keywords_to_check):
                print(16)
                return True
        elif (query[ind:ind+2].upper() == 'OR' or query[ind:ind+2].upper() =='ON') and query[ind + 2] == ' ' and query[ind - 1] == ' ':
            if ind + 2 > len(query):
                print(26)
                return True
            if query[ind+2] != ' ':
                print(27)
                return True
            keywords_to_check = ['FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT']

            if any(query[ind+2:ind+2+len(keyword)].strip().upper() == keyword for keyword in keywords_to_check):
                print(28)
                return True
        elif query[ind:ind+6].upper() == 'HAVING':
            if ind + 6 > len(query):
                print(20)
                return True
            if query[ind + 6] != ' ':
                print(21)
                return True
            keywords_to_check = ['FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT']

            if any(query[ind+6:ind+10].strip().upper() == keyword for keyword in keywords_to_check) or \
            any(query[ind+6:ind+12].strip().upper() == keyword for keyword in keywords_to_check):
                print(22)
                return True
        elif query[ind:ind+5].upper() == 'LIMIT':
            if ind + 5 > len(query):
                print(23)
                return True
            if query[ind+5] != ' ':
                print(24)
                return True
            keywords_to_check = ['FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT']

            substring = query[ind+5:ind+12].strip().upper()  # Adjusted to cover the longest keyword length

            if any(substring.startswith(keyword) for keyword in keywords_to_check):
                print(25)
                return True
        ind+=1

    return False


# main function
def main1(query):
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
        graph.render('node_structure1', format='png', cleanup=True)
        
        return 'node_structure1.png'

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
 
if __name__ == '__main__':
    query = "Select job_id, salary from job group by 1, 2"
    main1(query)
