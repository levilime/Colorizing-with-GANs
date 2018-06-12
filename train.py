from src import ModelOptions, main
print('start training')
options = ModelOptions().parse()
options.mode = 0
main(options)
