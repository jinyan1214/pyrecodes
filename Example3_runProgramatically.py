from pyrecodes import main
# system = main.run('./Example 3/NorthEast_SF_Housing_Main.json')
system = main.run('Example 4/NorthEast_SF_Housing_Interface_Infrastructure_Main.json')

system.calculate_resilience()