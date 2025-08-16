# **A Step-by-Step Guide to Building Scientific Software with PyMeasure**

This guide provides a structured approach to creating software for an experimental setup, leveraging the object-oriented principles and powerful features of the PyMeasure library. We will build the software from the ground up, starting with the most fundamental components.

## **Step 1: Create the Instrument Drivers 🛠️**

This is the most critical first step. Your software's foundation is built on reliable communication with your hardware.

**Goal**: Create a high-level Python class for each instrument that hides the low-level communication details.

**Project Structure**: Start by organizing your project files. This keeps your custom code separate from the PyMeasure library code, which is essential for future updates and reproducibility. This new structure is more detailed and scalable.

my\_experimental\_setup/  
├── instruments/  
│   ├── \_\_init\_\_.py  
│   ├── sourcemeter/  
│   │   ├── \_\_init\_\_.py  
│   │   └── my\_custom\_sourcemeter.py  
│   ├── daq/  
│   │   ├── \_\_init\_\_.py  
│   │   └── my\_custom\_daq.py  
│   └── ...  
├── procedures/  
│   ├── \_\_init\_\_.py  
│   └── iv\_sweep.py  
├── scripts/  
│   ├── \_\_init\_\_.py  
│   └── quick\_check.py  
└── main.py

**Inherit from pymeasure.instruments.Instrument**: For each instrument, create a Python file in its dedicated folder (e.g., sourcemeter/). In it, you'll define a class that inherits from the Instrument base class. This gives you access to core communication methods like read() and write().

**Use Properties**: Define the properties of your instruments (e.g., voltage, temperature, current limit) using the Instrument.control and Instrument.measurement methods. These properties handle sending and receiving commands to the instrument.

* Instrument.control: For attributes you can both set and read back. It takes a getter command and a setter command.  
* Instrument.measurement: For read-only attributes. It only takes a getter command.

**Test the Drivers**: Before writing any other code, create a small script to test each driver. Connect to the physical instrument and verify that you can read and write to all the properties correctly. This is your foundation; if this is not stable, nothing else will be.

## **Step 1.2: Create Modular Mock Drivers for Testing (Highly Recommended) 🧪**

Before connecting to the real instruments, create mock drivers that share the exact same API as the real ones. This allows you to develop, debug, and test your experimental logic and GUI without needing physical hardware.

**Goal**: Build a drop-in mock version of each driver that avoids code duplication and stays automatically in sync with your real driver’s methods and properties.

**Approach**: Use a MockInstrumentMixin that overrides only the hardware communication methods (write, read, ask) while inheriting everything else from the real driver.

**Implementation**: Create a file mock\_instrument.py in your instruments/ folder:

\# instruments/mock\_instrument.py  
import time  
import random

class MockInstrumentMixin:  
    """  
    A mixin to mock PyMeasure instrument communication methods.  
    Inherit from this \*before\* the real instrument class to override hardware I/O.  
    """  
    def \_\_init\_\_(self, \*args, \*\*kwargs):  
        \# Skip Instrument.\_\_init\_\_ to avoid actual hardware connection  
        pass

    def write(self, command):  
        print(f"\[MOCK WRITE\] {command}")

    def read(self):  
        time.sleep(0.05)  
        return str(random.uniform(0, 1))

    def ask(self, command):  
        self.write(command)  
        return self.read()

**Creating a Mock Driver from a Real Driver**:

from pymeasure.instruments.keithley import Keithley2400  
from instruments.mock\_instrument import MockInstrumentMixin

class MockKeithley2400(MockInstrumentMixin, Keithley2400):  
    pass

**Using the Mock Driver**:

USE\_MOCK \= True

if USE\_MOCK:  
    from instruments.mock\_drivers import MockKeithley2400 as Keithley2400  
else:  
    from pymeasure.instruments.keithley import Keithley2400

sourcemeter \= Keithley2400()  
print(sourcemeter.read())  \# Works without real hardware

**Advantages**:

* No duplication of high-level logic from the real driver.  
* Fully drop-in — all procedure code and GUIs work unchanged.  
* Safe to run anywhere (CI pipelines, laptops at home, etc.).  
* Realistic simulation of delays and variable readings.

## **Step 1.5: Build a Test GUI for Each Driver (Recommended) 🖥️**

This is an excellent way to test your drivers in isolation. By creating a simple GUI for each instrument, you can visually confirm that its functions are working as expected before integrating it into a larger experiment.

**Goal**: Create a standalone graphical interface for each instrument's driver.

**Create a GUI Script**: In the dedicated folder for each instrument (e.g., sourcemeter/), create a new Python file (e.g., test\_sourcemeter\_gui.py).

**Use Composition to Connect**: Inside the GUI script, create a class that instantiates your instrument driver. The buttons and input fields in the GUI will directly call the driver's methods and properties, allowing you to test functionality easily. This approach ensures your driver remains modular and separate from its user interface.

## **Step 2: Define Experiment Protocols 🔬**

Once your instrument drivers are working, you can define the logic for your experiments.

**Goal**: Create a reusable blueprint for each measurement or protocol you want to run.

**Inherit from pymeasure.experiment.Procedure**: In a new file within your procedures folder, create a class for each experiment. This class must inherit from Procedure.

**Define Parameters**: Use PyMeasure's Parameter classes (e.g., FloatParameter, IntegerParameter) as class variables. These parameters will be automatically used to create input fields in the graphical user interface.

**Implement Core Methods**:

* startup(): Called at the beginning of the experiment to configure and prepare your instruments.  
* execute(): The main loop of your experiment. This is where you will perform measurements and use self.emit('results', ...) to send data for saving and plotting. You must check self.should\_stop() within your loop to allow the experiment to be aborted.  
* shutdown(): Called at the end of the experiment (even if it's aborted or an error occurs) to safely return instruments to a safe state.

## **Step 3: Create the Global Setup Class (Recommended) 🌐**

This optional, but highly recommended, step creates a single point of entry for your entire experimental setup. It makes your code clean, modular, and easy to use.

**Goal**: Create a high-level class that "knows" about all the instruments and defines the available experiment protocols.

**Use Composition**: Your global class should not inherit from your instrument drivers. Instead, it should "contain" instances of them as attributes. This separates the responsibility of the overall setup from the individual instruments.

**Centralize Control**: In the \_\_init\_\_ method, instantiate all of your instrument drivers. You can also add a dictionary to track the current status of each instrument.

**Create High-Level Methods**: Add methods like run\_iv\_sweep() that act as wrappers to call and execute your Procedure objects. This allows a user to run a full experiment with a single, clear function call.

## **Step 4: Build the User Interface 🖥️**

Finally, you can build the user-facing part of your software, which will be surprisingly easy.

**Goal**: Create a functional and intuitive GUI for controlling your experiments without writing complex GUI code.

**Inherit from ManagedWindow**: The simplest and most powerful way to create a GUI is to inherit from pymeasure.display.windows.ManagedWindow.

**Link to Procedures**: In the constructor of your new window class, you simply tell the ManagedWindow which Procedure class you want to manage. PyMeasure automatically generates the input fields for all your parameters, a start/stop button, and a live plotting window.

This is where all your hard work pays off. The ManagedWindow handles the multi-threading, data saving, and plotting for you.

**Run the Application**: Use the standard PyQt5 boilerplate code to create the application instance and show your window.

