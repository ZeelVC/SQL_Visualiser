import sqlparse
from graphviz import Digraph
from flask import flash, render_template
#from .logic1 import check_syntax
 
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
 

def aggregate(str):
    present = False
    if str[0] == 'M' and str[1] == 'I' and str[2] == 'N' and str[3] == '(':
        present = True
    elif str[0] == 'M' and str[1] == 'A' and str[2] == 'X' and str[3] == '(':
        present = True
    elif str[0] == 'S' and str[1] == 'U' and str[2] == 'M' and str[3] == '(':
        present = True
    elif str[0] == 'A' and str[1] == 'V' and str[2] == 'G' and str[3] == '(':
        present = True
    elif str[0] == 'C' and str[1] == 'O' and str[2] == 'U' and str[3] == 'N' and str[4] == 'T' and str[5] == '(':
        present = True

    return present

def sql_to_graph(parsed, root, ind):
 
    #maintaining current_node
    current_node = root
    parent_node = root
    tableNode = Node('0')
    while ind < len(parsed):
        clause = parsed[ind]
        #close bracket code, indication there was a subquery
        if clause == ')':
            break
 
        #select condition
        elif clause.upper() == 'SELECT':
            ind+=1
            continue
 
        #From condition
        elif clause.upper() == 'FROM':
            if parsed[ind + 1] == '(':
                ind+=1
                continue
            else:
                tableNode = Node(parsed[ind + 1])
                j = ind + 2
                str = 'FROM\n\n( ' + parsed[ind + 1] 
                while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() != 'WHERE' and parsed[j].upper() != 'JOIN' and parsed[j].  upper() != 'GROUP' and parsed[j].upper() != 'ORDER' and parsed[j].upper() != 'LIMIT':
                    if parsed[j][len(parsed[j]) - 1] == ',':
                        str += parsed[j] + '\n'
                    else:
                        str += parsed[j] + ' '
                    j+=1
                str += ' )'
                tableNode.key_ele = str
 
        #Where condition
        elif clause.upper() == 'WHERE':
            j = ind + 1
            str = 'WHERE' + '\n\n( '
            isAfterAnd = False
            countAfterAnd = 0
            while j < len(parsed) and parsed[j].upper() != 'JOIN' and parsed[j].upper() != 'GROUP' and parsed[j].upper() != 'ORDER' and parsed[j].upper() != 'LIMIT':
                if parsed[j] == ')':
                    break
                if parsed[j] == '(':
                    if isAfterAnd == True:
                        countAfterAnd+=1
                    str+='subquery' + ' '
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
                    isAfterAnd = True
                    str += ' )'
                    temp = Node(str)
                    current_node.child.append(temp)
                    str = 'WHERE' + '\n\n( '
                else:
                    if parsed[j][len(parsed[j]) - 1] == ',':
                        str += parsed[j] + '\n'
                    else:
                        str += parsed[j] + ' '
                j+=1
            str += ' )'
            temp = Node(str)
            current_node.child.append(temp)


        #Join condition
        elif clause.upper() == 'JOIN':
            str = 'JOIN' + '\n\n( '
            j = ind + 1
            while parsed[j] != 'ON':
                j+=1
            while j < len(parsed) and parsed[j] != ')' and parsed[j] != 'WHERE' and parsed[j].upper() != 'GROUP' and parsed[j].upper() != 'JOIN':
                if parsed[j][len(parsed[j]) - 1] == ',' or parsed[j].upper() == 'AND' or parsed[j].upper() == 'OR':
                    str += parsed[j] + '\n'
                else:
                    str += parsed[j] + ' '
                j+=1
            str += ' )'
            temp = Node(str)
            temp.child.append(parent_node)
            parent_node = temp    
            if parsed[ind + 1] != '(':
                temp = Node(parsed[ind + 1])
                parent_node.child.append(temp)
 
        #group by condition
        elif clause.upper() == 'GROUP':
            j = ind + 2
            str = 'GROUP BY' + '\n\n( '
            while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() != 'HAVING' and parsed[j].upper() != 'ORDER' and parsed[j].upper() != 'LIMIT':
                if parsed[j][len(parsed[j]) - 1] == ',':
                    str += parsed[j] + '\n'
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
            while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() != 'ORDER' and parsed[j].upper() != 'LIMIT':
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
            str = 'ORDER BY' + '\n\n( '
            while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() != 'LIMIT':
                if parsed[j][len(parsed[j]) - 1] == ',':
                    str += parsed[j] + '\n'
                else:
                    str += parsed[j] + ' '
                j+=1
            str += ' )'
            temp = Node(str)
            temp.child.append(parent_node)
            parent_node = temp
 
        #LIMIT condition
        elif clause.upper() == 'LIMIT':
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
            root_subquery = Node('SELECT')
            j = ind + 2
            str = 'SELECT' + '\n\n( '
            aggr = 'AGGREGATE \n\n'
            isaggr = False
            while parsed[j].upper() != 'FROM':
                if aggregate(parsed[j].upper()):
                    aggr+= ' ' + parsed[j].upper()
                    isaggr = True
                elif parsed[j][len(parsed[j]) - 1] == ',':
                    str += parsed[j] + '\n'
                else:
                    str += parsed[j] + ' '
                j+=1
            str += ' )'
            root_subquery.key_ele = str
            root_subquery = sql_to_graph(parsed, root_subquery, ind + 2)
            if isaggr:
                temp = Node(aggr)
                temp.child.append(root_subquery)
                root_subquery = temp
            if parsed[ind - 1].upper() == 'FROM':
                tableNode = root_subquery
            elif parsed[ind - 1].upper() == 'WHERE' or parsed[ind - 1].upper() == 'AND' or parsed[ind - 1].upper() == 'OR' or parsed[ind - 1] == '=' or parsed[ind - 1] == '>' or parsed[ind - 1] == '<' or parsed[ind - 1] == 'IN' or parsed[ind - 1] == 'LIKE' or parsed[ind - 1] == 'AS' or parsed[ind - 1] == '!=':
                for node in current_node.child:
                    if node.key_ele.find('subquery') != -1 and len(node.child) == 0:
                        node.child.append(root_subquery)
                        break
            elif parsed[ind - 1].upper() == 'JOIN':
                parent_node.child.append(root_subquery)
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
            node.child.append(tableNode)
    else:
        current_node.child.append(tableNode)
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
    query1 = query
    #if check_syntax(query, 0):
     #   flash("SQL Syntax Error:", "error")
      #  return render_template("SQLViz.html")
    query = query1
    try:
        #query = "SELECT p1, p2, count(*) as numorders FROM ( SELECT op1.OrderID, op1.ProductID as p1, op2.ProductID as p2 FROM ( SELECT DISTINCT OrderID, ProductID FROM OrderLines ) op1 JOIN ( SELECT DISTINCT OrderID, ProductID FROM OrderLines ) op2 ON op1.OrderID = op2.OrderID AND op1.ProductID > op2.ProductID ) combinations JOIN ( SELECT job_address FROM job ) job ON salary_join GROUP BY p1, p2 LIMIT 10"
        
        #query = "SELECT emp_name, emp_id, dep_name FroM employee e Join department d ON e.department_id = d.department_id GROUP BY emp_name, emp_id HAVING sum(this) > 10 ORDER BY emp_name desc LIMIT 5"
        #query = "SELECT * FROM ( SELECT job_id FROM job ) employee e WHERE salary = ( SELECT MAX(salary) FROM department d ) JOIN department d ON e.department_id = d.department_id JOIN ( SELECT job_address FROM job ) job ON salary_join GROUP BY p1, p2"
        #query = "SELECT * FROM department d WHERE salary > 30000"
        #query = "SELECT emp_name, emp_id FROM ( SELECT MAX(salary) FROM employee ) combination GROUP BY p1. p1"
        #query = "SELECT op1.OrderID, op1.ProductID as p1, op2.ProductID as p2 FROM ( SELECT DISTINCT OrderID, ProductID FROM OrderLines ) op1 JOIN ( SELECT DISTINCT OrderID, ProductID FROM OrderLines ) op2 ON op1.OrderID = op2.OrderID AND op1.ProductID > op2.ProductID )"
        parsed = query.replace('\n', ' ').split()
        #print(parsed)
        root = Node('SELECT')
        i = 1
        str = 'SELECT' + '\n\n( '
        aggr = 'AGGREGATE \n\n'
        isaggr = False
        while parsed[i].upper() != 'FROM':
            if aggregate(parsed[i].upper()):
                aggr+=parsed[i].upper()+'\n\n'
                isaggr = True
            elif parsed[i][len(parsed[i]) - 1] == ',':
                str += parsed[i] + '\n'
            else:
                str += parsed[i] + ' '
            i+=1
        str += ' )'
        root.key_ele = str
        root = sql_to_graph(parsed, root, 0)
        if isaggr:
            temp = Node(aggr)
            temp.child.append(root)
            root = temp

        print_graph(root)
    
        graph = Digraph()
        root.visualize(graph)
        graph.render('node_structure2', format='png', cleanup=True)
        return f'{'node_structure2'}.png'
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
 
if __name__ == '__main__':
    query = "SELECT country, product, year, month, SUM(fold_count) as fold_count, COUNT(un) as device_count FROM `bigdata-user.avinash_t`.`BD240662_base` WHERE fold_count IS NOT NULL AND fold_count > 0 AND country IS NOT NULL GROUP BY 1,2,3,4 ORDER BY 1,2,3,4"
    main2(query)