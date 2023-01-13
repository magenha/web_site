import logging
def set_logging():
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        level=logging.INFO,
        datefmt='%m/%d/%Y %I:%M:%S %p'
        )
    logger = logging.getLogger('logger')
    logger.propagate = False
    fl = logging.FileHandler("spam.log")
    fl.setLevel(logging.INFO)
    logger.addHandler(fl)
    return logger

def function():
    global logger
    print('escribe algun numero')
    ans = int(input())
    if ans%2:
        logger.info('es impar')
    else:
        logger.info('es par')
        
if __name__ == "__main__":
    logger = set_logging()
    logger.info('finally')

    function()
    #logger.info('else')